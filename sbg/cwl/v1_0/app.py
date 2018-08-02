import os
import base64
from abc import abstractmethod
from sbg.cwl.v1_0.hints import is_empty
from sbg.cwl.v1_0.types import Primitive
from sbg.cwl.v1_0.base import Cwl, salad
from sbg.cwl.v1_0.hints import TypeFactory
from sbg.cwl.v1_0.check import to_str, to_list
from sbg.cwl.consts import (
    SBG_NAMESPACE, INHERIT_SINGLE, INHERIT_MULTI, EXPRESSION_LIB
)
from sbg.cwl.v1_0.requirement import (
    InlineJavascript, Docker, Resource, ShellCommand, EnvVar, InitialWorkDir,
    Software, SchemaDef, Dirent, EnvironmentDef
)
from sbg.cwl.v1_0.schema import (
    InputArray, InputEnum, InputRecord, OutputArray, OutputEnum, OutputRecord,
    OutputBinding, ArrayBase
)


@salad
def to_inputs(value, in_cls):
    """
    Converts value that can be either list|dict|JSON|$directive into CWL app
    inputs.
    """

    @salad
    def map_to_cls(obj):
        return in_cls(**obj)

    if value is not None:
        if isinstance(value, list):
            return list(map(map_to_cls, value))
        elif isinstance(value, dict):
            inputs = []
            for k, v in value.items():
                if isinstance(v, dict) and v.get('type'):
                    v = map_to_cls(v)
                    v.id = k
                else:
                    v = in_cls(id=k, type=v)
                inputs.append(v)
            return inputs
        else:
            raise TypeError('Unsupported type: {}'.format(type(value)))
    else:
        return []


@salad
def to_outputs(value, out_cls):
    """
    Converts value that can be either list|dict|JSON|$directive into CWL app
    outputs.
    """

    @salad
    def map_to_cls(obj):
        return out_cls(**obj)

    if value is not None:
        if isinstance(value, list):
            return list(map(map_to_cls, value))
        elif isinstance(value, dict):
            inputs = []
            for k, v in value.items():
                if isinstance(v, dict) and v.get('type'):
                    v = map_to_cls(v)
                    v.id = k
                else:
                    v = out_cls(id=k, type=v)
                inputs.append(v)
            return inputs
        else:
            raise TypeError('Unsupported type: {}'.format(type(value)))
    else:
        return []


class App(Cwl):
    """
    Super class for all runnable objects:
     - CommandLineTool
     - ExpressionTool
     - Workflow
    """

    def __init__(self, class_, cwl_version='v1.0', inputs=None, outputs=None,
                 id=None, requirements=None, hints=None, label=None, doc=None):
        super(App, self).__init__()
        self['class'] = class_
        self.cwl_version = cwl_version
        self.inputs = inputs
        self.outputs = outputs
        self.id = id
        self.requirements = requirements
        self.hints = hints
        self.label = label
        self.doc = doc

    # region abc
    @abstractmethod
    def _get_cls(self):
        """Get subclass class object."""
        pass

    @abstractmethod
    def _get_input_cls(self):
        """Get input class"""
        pass

    @abstractmethod
    def _get_output_cls(self):
        """Get output class"""
        pass

    # endregion

    # region utils

    def add_hints(self, *hints):
        """Adds application hints."""

        if not self.hints:
            self.hints = []
        self.hints += list(hints)

    def add_input_json(self):
        """
        Creates and adds ``input.json`` as workdir requirement.
        File ``input.json`` contains all information about inputs in runtime.
        """
        self.add_file(
            entryname='input.json',
            entry='$(JSON.stringify(inputs, null, 2))'
        )

    def find_requirement(self, name):
        """
        Returns requirement by class ``name``.
        """

        found = None
        if not self.requirements:
            self.requirements = []
        for x in self.requirements:
            if hasattr(x, 'class_') and x.class_ == name:
                found = x
                break
        return found

    def get_port(self, id):
        """
        Returns input/output port specified by id.

        :param id: IO unique identifier
        :return: IO port
        """
        found = self.get_input(id)
        if not found:
            found = self.get_output(id)
        return found

    def get_input(self, id):
        """
        Returns input by its ``id``.

        :param id: input id
        :return: input object
        """
        for i in self.inputs:
            if i.id == id:
                return i

    def get_output(self, id):
        """
        Returns output by its ``id``.

        :param id: output id
        :return: output object
        """

        for o in self.outputs:
            if o.id == id:
                return o

    def create_file(self, entry, entryname=None, writable=None, encode=False):
        """
        Returns created file (``Dirent``).

        :param entry: file content
        :param entryname: file name
        :param writable: flag that indicates that file is writable
        :param encode: encode entry using ``base64``
        :return: an instance of ``Dirent``
        """
        if encode:
            entry = base64.b64encode(entry.encode('utf-8')).decode("utf-8")

        return Dirent(entry, entryname=entryname, writable=writable)

    def add_file(self, entry, entryname=None, writable=None, encode=False):
        """
        Creates file (``Dirent``) and adds it into
        ``InitialWorkDirRequirement``.

        :param entry: file content
        :param entryname: file name
        :param writable: flag that indicates that file is writable
        :param encode: encode entry using ``base64``
        """

        self.add_in_workdir(self.create_file(
            entry, entryname=entryname, writable=writable, encode=encode
        ))

    def stage_input(self, id):
        """
        Stages input file specified by its ``id`` into current working dir.

        :param id: input file id
        """

        found = None
        if self.requirements:
            for r in self.requirements:
                if r.class_ == 'InitialWorkDirRequirement':
                    found = r
                    break

        stage = '$(inputs.{})'.format(id)
        if found:
            found.listing.append(stage)
        else:
            self.add_requirement(InitialWorkDir([stage]))

    def set_secondary_files(self, id, secondary):
        """
        Sets secondary files on input/output identified with `id`.

        :param id: object id
        :param secondary: provides a pattern or expression specifying files or
                          directories that must be included alongside the
                          primary file
        """
        port = self.get_port(id)
        if port:
            if isinstance(port, (self._get_input_cls(),
                                 self._get_output_cls())):
                port.secondary_files = secondary
            else:
                port['secondaryFiles'] = secondary

        else:
            raise ValueError('Object with id: {}, not found.'.format(
                id
            ))

    # endregion

    # region static methods

    @staticmethod
    def _get_inherit_expr(single, **kwargs):
        if single:
            return INHERIT_SINGLE.format(**kwargs)
        else:
            return INHERIT_MULTI.format(**kwargs)

    @staticmethod
    def _is_file_array(t):
        if isinstance(t, str) and t.rstrip('?') == '{}[]'.format(
                Primitive.FILE
        ):
            return True
        if isinstance(t, list):
            if Primitive.NULL in t:
                t.remove(Primitive.NULL)
            if len(t) > 0:
                t = t[0]
        if isinstance(t, ArrayBase) and t.items_ == Primitive.FILE:
            return True
        return False

    def inherit_metadata(self, src, dst):
        """
        Inherits metadata from ``src`` input id to ``dst`` output id.

        :param src: input ID
        :param dst: output ID
        """

        # add javascript expr lib
        self.add_expression_lib(EXPRESSION_LIB)

        found = None
        port = self.get_output(dst)
        single = not self._is_file_array(port.type)

        if isinstance(self.inputs, list):
            for o in self.outputs:
                if o.id == dst:
                    found = o
                    break
        else:
            found = self.outputs[dst]

        if found:
            ob = found.output_binding
            if not ob:
                ob = OutputBinding()
                found.output_binding = ob

            if ob.output_eval:
                if ob.output_eval.startswith('$('):  # inline expr
                    expr_self = ob.output_eval.lstrip('$(').rstrip(')').strip()
                    ob.output_eval = self._get_inherit_expr(
                        single,
                        input=src,
                        preprocess="self = {}".format(expr_self)
                    )
                else:
                    raise Exception(
                        "Can't set metadata inheritance, outputEval already "
                        "exists. Manual inheritance should be applied."
                    )
            else:
                ob.output_eval = self._get_inherit_expr(
                    single, input=src, preprocess=''
                )

    @staticmethod
    def add_sbg_namespace(app):
        """
        Adds SBG namespace for CWL application (tool, workflow).

        :param app: an instance of cwl.App
        :return: app with added SBG namespace
        """
        namespaces = app.get('$namespaces', dict())
        namespaces['sbg'] = SBG_NAMESPACE
        app['$namespaces'] = namespaces
        return app

    @staticmethod
    def set_required(obj, required):
        """
        If argument ``required=True`` return required object.
        If argument ``required=False`` return non required object.

        :param obj: type object
        :param required: flag
        :return: type object
        """
        if isinstance(obj, str):  # primitive
            obj = obj.rstrip('?')
            if not required:
                obj += '?'
        elif isinstance(obj, (InputRecord, InputEnum, InputArray, OutputRecord,
                              OutputEnum, OutputArray)):  # schema
            if not required:
                return ['null', obj]
            else:
                return obj
        elif isinstance(obj, list):  # union
            if not required:
                if Primitive.NULL not in obj:
                    obj.insert(0, Primitive.NULL)
                return obj
            else:
                obj.remove(Primitive.NULL)
                if len(obj) == 1:
                    obj = obj[0]
                return obj
        else:
            raise NotImplementedError(
                'Not implemented for type: {}'.format(type(obj))
            )
        return obj

    @staticmethod
    def is_required(obj):
        """
        Checks if obj is required type.

        :param obj: type object
        :return: bool
        """
        if isinstance(obj, list) and Primitive.NULL in obj:
            return False
        if isinstance(obj, str) and obj.endswith('?'):
            return False
        return True

    # endregion

    # region add requirement

    def add_expression_lib(self, lib):
        """
        Adds expression library into InlineJavascriptRequirement.

        :param lib: javascript library (can be string or list of strings)
        """

        if not self.requirements:
            self.requirements = []
        if os.path.isfile(lib):
            with open(lib, 'r') as fp_lib:
                expr = fp_lib.read()
        else:
            expr = lib
        inline_js = None
        for r in self.requirements:
            if isinstance(r, InlineJavascript):
                inline_js = r
                break
        if not inline_js:
            self.add_requirement(InlineJavascript(
                expression_lib=[expr])
            )
        else:
            if not inline_js.expression_lib:
                inline_js.expression_lib = []
            inline_js.expression_lib.append(expr)

    def add_env_var(self, env_name=None, env_value=None, env_def=None):
        """
        Adds environment variable into requirements.

        :param env_name: the environment variable name
        :param env_value: the environment variable value
        :param env_def: the list of environment variables
        """

        if env_def:
            var = env_def
        elif env_name and env_value:
            var = EnvironmentDef(env_name, env_value)
        else:
            raise ValueError(
                'Insufficient number of arguments.Specify either '
                '(env_name and env_value) or env_def'
            )

        found = self.find_requirement('EnvVarRequirement')
        if not found:
            self.add_requirement(EnvVar([var]))
        else:
            if isinstance(found.env_def, list):
                found.env_def.append(var)
            elif isinstance(found.env_def, dict):
                found.env_def[var.env_name] = var
            else:
                raise RuntimeError('Unsupported type: {}'.format(
                    type(found.envdef))
                )

    def add_in_workdir(self, r):
        """
        Adds ``r`` into InitialWorkDirRequirement.

        :param r: the list of files or subdirectories that must be placed in
                  the designated output directory prior to executing the
                  command line tool
        """

        found = None
        if not self.requirements:
            self.requirements = []
        for x in self.requirements:
            if (hasattr(x, 'class_') and
                    x.class_ == 'InitialWorkDirRequirement'):
                found = x
                break

        if found:
            found.listing += [r]
        else:
            self.add_requirement((InitialWorkDir(listing=[r])))

    def add_requirement(self, new_r):
        """Add ``new_r`` into requirements."""

        if isinstance(new_r, (InlineJavascript, SchemaDef, Docker, Software,
                              InitialWorkDir, EnvVar, ShellCommand, Resource)):
            updated = False
            if self.requirements:
                for r in self.requirements:
                    if r.class_ == new_r.class_:
                        r.update(new_r)
                        updated = True
                if not updated:
                    self.requirements.append(new_r)
            else:
                self.requirements = [new_r]
        else:
            raise TypeError('Expected Requirement got: {}'.format(type(new_r)))

    # endregion

    # region io
    def _io_common(self, hint, io):
        """Extracts and sets common fields for IO."""
        if hint.label:
            io.label = hint.label
        if hint.doc:
            io.doc = hint.doc
        if hint.secondary_files:
            io.secondary_files = hint.secondary_files
        return io

    def add_input(self, hint, id=None, label=None, secondary_files=None,
                  streamable=None, doc=None, format=None, input_binding=None,
                  stage=False):
        """
        Adds input by type hint and kwargs arguments.

        :param hint: type hint (eg, ``Int()``, ``String()``, etc)
        :param id: the unique identifier for this parameter object
        :param label: a short, human-readable label of this object
        :param secondary_files: a list of additional files or directories that
                                are associated with the primary file and must
                                be transferred alongside the primary file
        :param streamable: a value of true indicates that the file is read or
                           written sequentially without seeking
        :param doc: a documentation string for this type,
                    or an array of strings which should be concatenated
        :param format: the format of the file
        :param input_binding: describes how to handle the inputs of a process
                              and convert them into a concrete form for
                              execution, such as command line parameters.
        :param stage: stages input file into current working dir
        """

        default = None if is_empty(hint.default) else hint.default

        input = self._io_common(hint, self._get_input_cls()(
            id=id, label=label, secondary_files=secondary_files,
            streamable=streamable, doc=doc, format=format,
            input_binding=input_binding, default=default,
            type=TypeFactory.create(hint, True)
        ))

        if not self.inputs:
            self.inputs = []
        self.inputs.append(input)
        if stage:
            self.stage_input(id)
        return input

    def add_output(self, hint, id=None, label=None, secondary_files=None,
                   streamable=None, doc=None, output_binding=None,
                   format=None):
        """
        Adds output by type hint and kwargs arguments.

        :param id: the unique identifier for this parameter object
        :param label: a short, human-readable label of this object
        :param secondary_files: provides a pattern or expression specifying
                                files or directories that must be included
                                alongside the primary file.
        :param streamable: a value of true indicates that the file is read or
                           written sequentially without seeking
        :param doc: a documentation string for this type,
                    or an array of strings which should be concatenated
        :param output_binding: describes how to handle the outputs of a process
        :param format: the format of the file
        """

        if hint.glob and not output_binding:
            output_binding = OutputBinding(glob=hint.glob)

        output = self._io_common(hint, self._get_output_cls()(
            id=id, label=label, secondary_files=secondary_files,
            streamable=streamable, doc=doc, format=format,
            output_binding=output_binding, type=TypeFactory.create(hint, False)
        ))

        if not self.outputs:
            self.outputs = []
        self.outputs.append(output)
        return output

    # endregion

    # region properties

    @property
    def inputs(self):
        """
        Defines the input parameters of the process. The process is ready to
        run when all required input parameters are associated with concrete
        values. Input parameters include a schema for each parameter which is
        used to validate the input object. It may also be used to build a user
        interface for constructing the input object.

        When accepting an input object, all input parameters must have a value.
        If an input parameter is missing from the input object, it must be
        assigned a value of null (or the value of default for that parameter,
        if provided) for the purposes of validation and evaluation of
        expressions.
        """
        return self.get('inputs')

    @inputs.setter
    def inputs(self, value):
        self['inputs'] = to_inputs(value, self._get_input_cls())

    @property
    def outputs(self):
        """
        Defines the parameters representing the output of the process.
        May be used to generate and/or validate the output object.
        """
        return self.get('outputs')

    @outputs.setter
    def outputs(self, value):
        self['outputs'] = to_outputs(value, self._get_output_cls())

    @property
    def id(self):
        """The unique identifier for this process object."""
        return self.get('id')

    @id.setter
    def id(self, value):
        self['id'] = to_str(value)

    @property
    def requirements(self):
        """
        Declares requirement that apply to either the runtime environment or
        the wf engine that must be met in order to execute this process.
        If an implementation cannot satisfy all requirement, or a requirement
        is listed which is not recognized by the implementation, it is a fatal
        error and the implementation must not attempt to run the process,
        unless overridden at user option.
        """
        return self.get('requirements')

    @abstractmethod
    def get_requirements(self, value):
        pass

    @requirements.setter
    def requirements(self, value):
        self['requirements'] = self.get_requirements(value)

    @property
    def hints(self):
        """
        Declares hints applying to either the runtime environment or the
        wf engine that may be helpful in executing this process.
        It is not an error if an implementation cannot satisfy all hints,
        however the implementation may report a warning.
        """
        return self.get('hints')

    @hints.setter
    def hints(self, value):
        self['hints'] = to_list(value)

    @property
    def label(self):
        """A short, human-readable label of this process object."""
        return self.get('label')

    @label.setter
    def label(self, value):
        self['label'] = to_str(value)

    @property
    def doc(self):
        """A long, human-readable description of this process object."""
        return self.get('doc')

    @doc.setter
    def doc(self, value):
        self['doc'] = to_str(value)

    @property
    def cwl_version(self):
        """
        CWL document version. Always required at the document root.
        Not required for a Process embedded inside another Process.
        """
        return self.get('cwlVersion')

    @cwl_version.setter
    def cwl_version(self, value):
        self['cwlVersion'] = to_str(value)
    # endregion
