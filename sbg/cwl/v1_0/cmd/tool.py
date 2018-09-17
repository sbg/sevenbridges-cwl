import os
import re
import shutil
import inspect
import collections
from sbg.cwl import serialize
from sbg.cwl.v1_0.app import App
from sbg.cwl.sbg.hints import SaveLogs
from sbg.cwl.v1_0.base import salad
from sbg.cwl.serialize import consts
from sbg.cwl.serialize import deploy
from sbg.cwl.v1_0.cmd.input import CommandInput
from sbg.cwl.v1_0.cmd.output import CommandOutput
from sbg.cwl.consts import BASH_BUNDLE_NAME, BASH_LIB
from sbg.cwl.serialize.consts import OUT_PATH, UTIL_PATH
from sbg.cwl.v1_0.schema import InputBinding, OutputBinding
from sbg.cwl.v1_0.check import to_str_slist, to_str, to_ilist
from sbg.cwl.v1_0.util import (
    is_instance_all, is_instance_all_dict, archive
)
from sbg.cwl.v1_0.hints import (
    String, Int, Float, Bool, Any, Hint, File, Dir, Array, Union, Enum,
    is_empty
)
from sbg.cwl.v1_0.requirement import (
    InitialWorkDir, SchemaDef, Software, EnvVar, ShellCommand, Resource,
    Docker, InlineJavascript, Dirent
)

DEFAULT_ARG = (
    '''parser.add_argument('{prefix}', type=json.loads, action='store',\n'''
    '''                    required={required!r}, default={default!r})'''
)


@salad
def to_cmd_req(obj):
    """Converts object to CommandLineTool requirement."""

    m = dict(
        InlineJavascriptRequirement=InlineJavascript,
        SchemaDefRequirement=SchemaDef,
        DockerRequirement=Docker,
        SoftwareRequirement=Software,
        InitialWorkDirRequirement=InitialWorkDir,
        EnvVarRequirement=EnvVar,
        ShellCommandRequirement=ShellCommand,
        ResourceRequirement=Resource

    )
    if isinstance(obj, dict):
        if 'class' in obj:
            return m[obj['class']](**obj)
        else:
            raise ValueError("Missing class, {}".format(obj))
    else:
        raise ValueError("Expected dict, found: {}".format(type(obj)))


@salad
def to_salad_obj(value):
    return value


@salad
def get_requirements(value):
    """Converts value to CommandLineTool requirements."""

    if value is not None:
        if is_instance_all(value,
                           InlineJavascript, SchemaDef, Docker, Software,
                           InitialWorkDir, EnvVar, ShellCommand, Resource):
            return value
        elif is_instance_all_dict(
                value, InlineJavascript, SchemaDef, Docker, Software,
                InitialWorkDir, EnvVar, ShellCommand, Resource
        ):
            return value
        elif isinstance(value, list):
            return list(map(to_cmd_req, value))
        elif isinstance(value, dict):
            return {k: to_salad_obj(v) for k, v in value.items()}
        else:
            raise ValueError("Expected list, got {}.".format(type(value)))


@salad
def to_str_ibinding(value):
    """Converts list of values to list of str|input_binding|$directive"""

    @salad
    def map_obj(obj):
        if isinstance(obj, str):
            return obj
        return InputBinding(**obj)

    if value is not None:
        if is_instance_all(value, str, InputBinding):
            return value
        elif isinstance(value, list):
            return list(map(map_obj, value))
        else:
            raise TypeError('Expected list, got {}'.format(type(value)))


class CommandLineTool(App):
    """
    This defines the schema of the CWL Command Line Tool Description document.
    """
    class_ = 'CommandLineTool'

    def __init__(self, cwl_version='v1.0',
                 inputs=None, outputs=None, id=None, requirements=None,
                 hints=None, label=None, doc=None, base_command=None,
                 arguments=None, stdin=None, stdout=None, stderr=None,
                 success_codes=None, temporary_fail_codes=None,
                 permanent_fail_codes=None, **kwargs):
        super(CommandLineTool, self).__init__(self.class_,
                                              cwl_version=cwl_version,
                                              inputs=inputs, outputs=outputs,
                                              id=id, requirements=requirements,
                                              hints=hints, label=label, doc=doc
                                              )
        self.base_command = base_command
        self.arguments = arguments
        self.stderr = stderr
        self.stdin = stdin
        self.stdout = stdout
        self.success_codes = success_codes
        self.temporary_fail_codes = temporary_fail_codes
        self.permanent_fail_codes = permanent_fail_codes

        self.type_map = {
            bool: Bool(),
            float: Float(),
            int: Int(),
            str: String(),
            None: Any()
        }

    # region utils

    def unarchive_bundle(self, bundle, encoded=False, postprocess=None):
        """
        Adds first unarchiving command as first argument. It can also decode
        base64 encoded bundles.

        :param bundle: bundle name
        :param encoded: flag which indicates that ``bundle`` is base64 encoded
        """
        m = 0
        if self.arguments:
            positions = {
                arg.position if isinstance(arg, InputBinding) else 0
                for arg in self.arguments
            }
            m = min(map(lambda p: p if p else 0, positions))
        else:
            self.arguments = []
        ib = self.get_unarchive_argument(
            bundle, encoded=encoded, postprocess=postprocess
        )
        if m != 0:
            ib.position = m
        self.arguments.insert(0, ib)

    @staticmethod
    def get_unarchive_argument(bundle, encoded=False, postprocess=None):
        """
        Returns ``InputBinding`` argument with untar command.

        :param bundle: archive name
        :param encoded: flag which indicates that ``bundle`` is base64 encoded
        :return: an instance of ``InputBinding`` which is an argument
        """

        ib = InputBinding(
            shell_quote=False,
            value_from='cat {name} {decode}| tar xjf - ; {proc}'.format(
                decode='| base64 --decode ' if encoded else '',
                name=bundle,
                proc="{} ;".format(
                    postprocess.rstrip(';')
                ) if postprocess else ''
            )
        )
        return ib

    def _inputs_from_f(self, f):
        """Gets input list from function `f`."""

        sig = inspect.signature(f)
        f_args = dict(sig.parameters)
        inputs = []
        annotations = None

        if hasattr(f, 'to_tool_args'):
            annotations = f.to_tool_args['inputs']

        for k, v in f_args.items():
            type_ = None
            if annotations:
                type_ = annotations[k]
            elif v.annotation != inspect._empty:
                if v.annotation in self.type_map:
                    type_ = self.type_map[v.annotation]
                else:
                    type_ = v.annotation

            if not is_empty(v.default):
                type_.default = v.default

            if (isinstance(type_, collections.Hashable) and
                    type_ in self.type_map):
                type_ = self.type_map[type_]
            elif not isinstance(type_, Hint):
                raise RuntimeError(
                    'Invalid type hint: {}'.format(type_)
                )

            inputs.append({
                'id': k,
                'type': type_
            })

        return inputs

    def _outputs_from_f(self, f):
        """Gets output list from function `f`."""

        outputs = []
        sig = inspect.signature(f)
        if hasattr(f, 'to_tool_args') and f.to_tool_args['outputs']:
            out = f.to_tool_args['outputs']
        else:
            out = sig.return_annotation
        if not out == sig.empty:
            if not isinstance(out, dict):
                raise ValueError('Output annotation have to be dict.')

            for k, annotation in out.items():
                type_ = None
                if annotation != inspect._empty:
                    type_ = annotation

                if (isinstance(type_, collections.Hashable) and
                        type_ in self.type_map):
                    type_ = self.type_map[type_]
                elif not isinstance(type_, Hint):
                    raise RuntimeError(
                        'Invalid type hint: {}'.format(type_)
                    )
                outputs.append({
                    'id': k,
                    'type': type_
                })

        return outputs

    def _set_inputs_from(self, f):
        """Sets inputs from annotated python function."""

        inputs = self._inputs_from_f(f)
        for i in inputs:
            id = i['id']
            label = i['id']
            i['type'].required = is_empty(i['type'].default)
            self.add_input(i['type'], id=id, label=label)
            self.add_requirement(InlineJavascript())
            self.add_requirement(ShellCommand())

    def _set_outputs_from(self, f):
        """Sets outputs from annotated python function."""

        outputs = self._outputs_from_f(f)
        for o in outputs:
            id = o['id']
            label = id

            if o['type'].glob:
                glob = o['type'].glob
                load_contents = None
                oe = None
            else:
                glob = OUT_PATH
                load_contents = True
                oe = "$(JSON.parse(self[0].contents)['{id}'])".format(
                    id=id
                )
            self.add_output(
                o['type'], id=id, label=label, output_binding=OutputBinding(
                    glob=glob,
                    output_eval=oe,
                    load_contents=load_contents
                )
            )

    def _create_parser(self, inputs):
        """Creates argparse code block by specified `inputs`."""

        args = []
        for i in inputs:
            args.append(DEFAULT_ARG.format(
                prefix='--{}'.format(i.id),
                required=App.is_required(i.type),
                default=i.default if not is_empty(i.default) else None
            ))
        return '\n'.join(args)

    def _listing_from_f(self, func, name):
        """
        Sets all init workdir requirements necessary for running python
        function `f`.
        """

        def rrm_pycache(dir):
            for root, dirs, _ in os.walk(dir):
                for name in dirs:
                    if name == '__pycache__':
                        shutil.rmtree(os.path.join(root, name))
                    else:
                        rrm_pycache(os.path.join(root, name))

        def rm_pycache(modules, working_dir):
            for m in {os.path.join(working_dir, m) for m in modules}:
                rrm_pycache(m)

        def tar_modules(modules, extra=None):
            """Create a tar file of provided module list with paths, inside the
            tar, are relative to the working_dir.
            """

            working_dir = os.getcwd()
            modules = {
                # Get only the direct children of the working_dir
                # tar module will do the recursive packaging
                m.replace(working_dir, '', 1).lstrip('/').split('/')[0]
                for m in modules
            }
            rm_pycache(modules, working_dir)
            arcnames = dict()
            for obj in sorted(extra):
                if os.path.isfile(obj['path']):
                    modules.add(obj['path'])
                    arcnames[obj['path']] = obj['name']
            return archive(modules, encode=True, arcnames=arcnames)

        context = serialize.Context(func)
        context.add(name, func)

        util_file = deploy.__file__

        return [
            self.create_file(
                entryname="{}.py.b64".format(name),
                entry=consts.SCAFOLD.format(
                    archive_name=name,
                    b64untar=inspect.getsource(deploy.b64untar),
                    imports='\n'.join(context.create_imports()),
                    variables='\n\n'.join(context.create_variables()),
                    functions='\n\n'.join(context.create_functions()),
                    classes='\n\n'.join(context.create_classes()),
                    function=func.__name__
                ),
                encode=True
            ),
            Dirent(
                entryname='{}.tar.bz2.b64'.format(name),
                entry=tar_modules(context.modules, extra=[
                    dict(
                        name=UTIL_PATH,
                        path=util_file
                    )
                ])
            )
        ]

    def _create_file_from(self, f, name=None):
        """
        Creates all init workdir requirements necessary for running python
        function `f`.
        """
        if not name:
            name = f.__name__
        for r in self._listing_from_f(f, name):
            self.add_in_workdir(r)

    def add_locals(self, locals, name, postprocess=None):
        """
        Add local files/dirs to tool in runtime.

        :param locals: list with paths
        :param name: bundle name in runtime
        :param postprocess: bash operation after unarchiving a bundle
        """

        names = list(map(os.path.abspath, locals))
        entry = archive(names, encode=True)
        self.add_file(entry=entry, entryname=name)
        self.unarchive_bundle(
            bundle=name, encoded=True, postprocess=postprocess
        )

        if not self.hints:
            self.hints = []

        self.hints.append(SaveLogs(os.path.basename(name)))
        for l in locals:
            if os.path.isfile(l):
                self.hints.append(SaveLogs(os.path.basename(l)))

    @staticmethod
    def _create_var(t, env_name, env_val):
        other_expr = "$((inputs.{env_name})?inputs.{env_name}:'')"
        fd_expr = "$((inputs.{env_name})?inputs.{env_name}.path:'')"
        arr_fd_expr = "$((inputs.{env_name})?inputs.{env_name}" \
                      ".map(function(x){{return x['path']}})" \
                      ".join(' '): '')"
        arr_other_expr = "$((inputs.{env_name})?inputs.{env_name}" \
                         ".join(' '):'')"
        hint = None
        if isinstance(env_val, str):  # hardcode env
            t.add_env_var(
                env_name=env_name,
                env_value=env_val
            )
        # create input and connect with env variable
        elif isinstance(env_val, Hint):
            hint = env_val
            if isinstance(
                    env_val, (String, Int, Float, Bool, Any, Union, Enum)
            ):
                t.add_env_var(
                    env_name=env_name,
                    env_value=other_expr.format(
                        env_name=env_name
                    )
                )
            elif isinstance(env_val, (File, Dir)):
                t.add_env_var(
                    env_name=env_name,
                    env_value=fd_expr.format(
                        env_name=env_name
                    )
                )
            elif isinstance(env_val, Array):
                if isinstance(env_val.val, (File, Dir)):
                    t.add_env_var(
                        env_name=env_name,
                        env_value=arr_fd_expr.format(
                            env_name=env_name
                        )
                    )
                else:
                    t.add_env_var(
                        env_name=env_name,
                        env_value=arr_other_expr.format(
                            env_name=env_name
                        )
                    )
            else:
                raise NotImplementedError(
                    'Not implemented for {}'.format(
                        env_val
                    )
                )
        else:
            raise ValueError(
                'Unsupported env_val: {}'.format(
                    env_val
                )
            )
        if hint:
            t.add_input(
                hint,
                id=env_name,
                label=env_name
            )

    @classmethod
    def from_bash(cls, script, name='script.sh', id=None, label=None, doc=None,
                  inputs=None, outputs=None, sources=None, lib=None,
                  docker=None, secondary_files=None, stdout=None):
        """
        Creates CommandLineTool created from bash script.

        :param script: can be bash file or contents
        :param name: bash script name
        :param id: tool ID
        :param label: tool label
        :param doc: tool description
        :param inputs: dictionary where keys are variable names and values
                       can be either one of cwl hints or string.
                       if hint is specified, then corresponding input will
                       be created.
                       If string is specified, then environment variable
                       with that string value will be created.
        :param outputs: dictionary where keys are output ids and values
                        are cwl hints
        :param sources: executes ``source <source>`` which can be used for
                        exporting bash variables
        :param lib: only required when sources are specified, used as a name
                    for bundle with sources
        :param docker: specify a docker image to retrieve using docker pull
        :param secondary_files: dictionary where key is input/output id and
                                value is secondary files
        :param stdout: standard output redirect to this file
        :return: an instance of ``cwl.CommandLineTool``
        """
        if not lib:
            lib = BASH_BUNDLE_NAME
        if not sources:
            sources = []
        sources.append(BASH_LIB)

        t = CommandLineTool()
        if id:
            t.id = id
        if label:
            t.label = label
            if not t.id:
                t.id = '_'.join(map(str.lower, re.findall(r"\w+", label)))
        if doc:
            t.doc = doc
        if os.path.isfile(script):
            with open(script, 'r') as fp:
                if not name:
                    name = os.path.basename(script)
                entry = fp.read()
        elif isinstance(script, str):
            if not name:
                raise ValueError(
                    'Missing name for bash script.'
                )
            entry = script
        else:
            raise ValueError(
                'Illegal value for arugment script.'
            )
        entry_name = "{}.b64".format(name)
        t.add_file(
            entryname=entry_name,
            entry=entry,
            encode=True
        )
        if sources:
            if not lib or not isinstance(lib, str):
                raise ValueError(
                    'Argument lib should be provided when sources are used.'
                )
            t.add_locals(sources, lib)
            sources_str = ''.join(map(
                lambda x: "source {} && ".format(
                    os.path.basename(x)
                ), sources)
            )
        else:
            t.arguments = []
            sources_str = ''
        bash_inline = \
            '{sources} cat {encoded_script}|' \
            'base64 --decode > {script} && ' \
            '/bin/bash ./{script}'.format(
                sources=sources_str if sources else '',
                encoded_script=entry_name,
                script=name
            )
        t.arguments.append(
            InputBinding(
                shell_quote=False,
                value_from='/bin/bash -c "{inline}"'.format(
                    inline=bash_inline
                )
            )
        )
        t.add_requirement(Docker(docker_pull=docker))
        t.add_requirement(ShellCommand())
        t.add_requirement(InlineJavascript())
        if inputs:
            for env_name, env_val in inputs.items():
                cls._create_var(t, env_name, env_val)

        if outputs:
            for k, v in outputs.items():
                t.add_output(v, id=k, label=k)
        if stdout:
            t.stdout = stdout

        if secondary_files:
            if not isinstance(secondary_files, dict):
                raise ValueError(
                    'Secondary files argument have to be an instance of dict'
                )
            for k, v in secondary_files.items():
                t.set_secondary_files(k, v)

        t.add_input_json()
        t.hints = [
            SaveLogs(os.path.basename(name)),  # main bash script
        ]
        for s in sources:
            t.hints.append(SaveLogs(os.path.basename(s)))  # all sources

        if stdout:
            t.hints.append(SaveLogs(stdout))

        # add SBG namespace
        t = cls.add_sbg_namespace(t)
        return t

    # endregion

    # region override
    def get_requirements(self, value):
        return get_requirements(value)

    def _get_cls(self):
        return CommandLineTool

    def _get_input_cls(self):
        return CommandInput

    def _get_output_cls(self):
        return CommandOutput

    # endregion

    # region properties

    @property
    def base_command(self):
        """
        Specifies the program to execute. If an array, the first element of the
        array is the command to execute, and subsequent elements are mandatory
        command line arguments. The elements in baseCommand must appear before
        any command line bindings from inputBinding or arguments.

        If baseCommand is not provided or is an empty array, the first element
        of the command line produced after processing inputBinding or arguments
        must be used as the program to execute.

        If the program includes a path separator character it must be an
        absolute path, otherwise it is an error. If the program does not
        include a path separator, search the $PATH variable in the runtime
        environment of the wf runner find the absolute path of the
        executable.
        """
        return self.get('baseCommand')

    @base_command.setter
    def base_command(self, value):
        self['baseCommand'] = to_str_slist(value)

    @property
    def arguments(self):
        """
        Command line bindings which are not directly associated
        with input parameters.
        """
        return self.get('arguments')

    @arguments.setter
    def arguments(self, value):
        self['arguments'] = to_str_ibinding(value)

    @property
    def stdin(self):
        """
        A path to a file whose contents must be piped into the
        command's standard input stream.
        """
        return self.get('stdin')

    @stdin.setter
    def stdin(self, value):
        self['stdin'] = to_str(value)

    @property
    def stdout(self):
        """
        Capture the command's standard output stream to a file written to
        the designated output directory.

        If stdout is a string, it specifies the file name to use.

        If stdout is an expression, the expression is evaluated and must return
        a string with the file name to use to capture stdout. If the return
        value is not a string, or the resulting path contains illegal
        characters (such as the path separator /) it is an error.
        """
        return self.get('stdout')

    @stdout.setter
    def stdout(self, value):
        self['stdout'] = to_str(value)

    @property
    def stderr(self):
        """
        Capture the command's standard error stream to a file written to the
        designated output directory.

        If stderr is a string, it specifies the file name to use.

        If stderr is an expression, the expression is evaluated and must return
        a string with the file name to use to capture stderr. If the return
        value is not a string, or the resulting path contains illegal
        characters (such as the path separator /) it is an error.
        """
        return self.get('stderr')

    @stderr.setter
    def stderr(self, value):
        self['stderr'] = to_str(value)

    @property
    def success_codes(self):
        """Exit codes that indicate the process completed successfully."""
        return self.get('successCodes')

    @success_codes.setter
    def success_codes(self, value):
        self['successCodes'] = to_ilist(value)

    @property
    def temporary_fail_codes(self):
        """
        Exit codes that indicate the process failed due to a possibly
        temporary condition, where executing the process with the same runtime
        environment and inputs may produce different results.
        """
        return self.get('temporaryFailCodes')

    @temporary_fail_codes.setter
    def temporary_fail_codes(self, value):
        self['temporaryFailCodes'] = to_ilist(value)

    @property
    def permanent_fail_codes(self):
        """
        Exit codes that indicate the process failed due to a permanent logic
        error, where executing the process with the same runtime environment
        and same inputs is expected to always fail.
        """
        return self.get('permanentFailCodes')

    @permanent_fail_codes.setter
    def permanent_fail_codes(self, value):
        self['permanentFailCodes'] = to_ilist(value)

    # endregion
