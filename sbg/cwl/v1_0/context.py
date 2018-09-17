import sys
import inspect
import functools
from contextlib import contextmanager
from sbg.cwl.v1_0.util import from_file
from sbg.cwl.v1_0.schema import InputBinding
from sbg.cwl.v1_0.wf.workflow import Workflow
from sbg.cwl.v1_0.cmd.tool import CommandLineTool
from sbg.cwl.v1_0.requirement.docker import Docker
from sbg.cwl.v1_0.requirement.shell_command import ShellCommand
from sbg.cwl.v1_0.requirement.inline_javascript import (
    InlineJavascript
)


def _tool_from(t, f):
    """Generates an instance of CommandLineTool from annotated function."""

    doc = inspect.getdoc(f)
    if doc:
        t.doc = doc
    if hasattr(f, '__name__'):
        t.id = f.__name__
        t.label = f.__name__

    t._set_inputs_from(f)
    t._set_outputs_from(f)

    py_info = sys.version_info
    py = "python{major}.{minor}".format(
        major=py_info.major,
        minor=py_info.minor
    )
    encoded_script = '{}.py.b64'.format(f.__name__)
    t.arguments = [
        InputBinding(
            shell_quote=False,
            value_from='cat {encoded_script}|'.format(
                encoded_script=encoded_script
            )
        ),
        InputBinding(
            shell_quote=False,
            value_from='base64 --decode > {script};'.format(
                script=encoded_script.rstrip('.b64')
            )
        ),
        py, "{}.py".format(f.__name__)
    ]
    t._create_file_from(f)
    t.add_input_json()
    return t


def ctx_enter(cls, path, access):
    """
    Function on context enter.

    :param cls: ``class`` object
    :param path: file path
    :param access: access permission ('r' - read, 'w' - write, 'rw' - edit)
    :return: an instance of ``cls``
    """
    obj = None
    if path and 'r' in access:
        cwl = from_file(path)
        if isinstance(cwl, dict):
            if "class" in cwl:
                if cwl['class'] == cls.__name__:
                    obj = cls(**cwl)
                else:
                    raise ValueError(
                        "Expected class={}, got class={}".format(
                            cls.__name__, cwl['class'])
                    )
            else:
                raise ValueError("Missing class key.")
        else:
            raise ValueError('Type Error, got: {}'.format(type(cwl)))
    if not obj:
        obj = cls()
    return obj


def ctx_exit(obj, path, access):
    """
    Called on context exit. if ``access='w'`` dumps ``obj`` into
    file specified by ``path``.

    :param obj: object to be dumped
    :param path: file path
    :param access: access permission ('r' - read, 'w' - write, 'rw' - edit)
    """
    if 'w' in access:
        obj.dump(path)


@contextmanager
def tool(path=None, access='r'):
    """
    Class that can be used with ``with`` statement for reading/writing/editing
    tool.

    :param path: file path
    :param access: access permission ('r' - read, 'w' - write, 'rw' - edit)

    Example of writing:

    .. code-block:: python

       from sbg import cwl

       with cwl.tool('example.cwl', 'w') as t:
           t.id = 'tool_id'       #  set id
           t.label = 'Dummy tool' #  set label

    Example of reading:

    .. code-block:: python

       from sbg import cwl

       with cwl.tool('example.cwl', 'r') as t:
           print(' '.join(t.base_command)) #  print base command

    Example of editing:

    .. code-block:: python

       from sbg import cwl

       with cwl.tool('example.cwl', 'rw') as t:
           t.doc = 'New description...' #  edit tool description

    """
    obj = ctx_enter(CommandLineTool, path, access)
    yield obj
    ctx_exit(obj, path, access)


@contextmanager
def workflow(path=None, access='r'):
    """
    Class that can be used with ``with`` statement for reading/writing/editing
    workflow.

    :param path: file path
    :param access: access permission ('r' - read, 'w' - write, 'rw' - edit)

    Example of writing:

    .. code-block:: python

       from sbg import cwl

       with cwl.workflow('example.cwl', 'w') as wf:
           wf.id = 'workflow_id'       #  set id
           wf.label = 'Dummy workflow' #  set label

    Example of reading:

    .. code-block:: python

       from sbg import cwl

       with cwl.workflow('example.cwl', 'r') as wf:
           for step in wf.steps: #  print workflow steps
               print(step)

    Example of editing:

    .. code-block:: python

       from sbg import cwl

       with cwl.workflow('example.cwl', 'rw') as wf:
           wf.doc = 'New description...' #  edit workflow description

    """
    obj = ctx_enter(Workflow, path, access)
    yield obj
    ctx_exit(obj, path, access)


@contextmanager
def tool_from(f, path=None, access='r'):
    """
    Class that can be used with ``with`` statement for reading/writing/editing
    tool from function ``f``.

    :param f: function
    :param path: file path
    :param access: access permission ('r' - read, 'w' - write, 'rw' - edit)

    Example:

     .. code-block:: python

        from sbg import cwl

        def multiply(x: cwl.Int(), y: cwl.Int()) -> dict(out=cwl.Int()):
           return dict(out=x * y)

        # creates CWL application from function multiply
        with cwl.tool_from(multiply, 'multiply.cwl', 'w') as t:
           t.add_docker_requirement(
               docker_pull='<docker_with_python>'
           )
    """
    obj = _tool_from(ctx_enter(CommandLineTool, path, access), f)
    yield obj
    ctx_exit(obj, path, access)


def to_tool(
        # constructor arguments
        inputs=None, outputs=None, id=None, requirements=None,
        hints=None, label=None, doc=None, base_command=None,
        arguments=None, stdin=None, stdout=None, stderr=None,
        success_codes=None, temporary_fail_codes=None,
        permanent_fail_codes=None,

        # helpers
        docker=None,  # Docker image
        js=True,  # Add InlineJavascriptRequirement
        sh=True  # Add ShellCommandRequirement
):
    """
    .. decorator:: to_tool

    Decorator for creating tool from a function.

    :param inputs: annotated inputs represented as a dictionary, where
                   keys=inputs and values=types
    :param outputs: annotated outputs represented as a dictionary, where
                    keys=outputs and values=types
    :param id: id of a tool (default name of a decorated function)
    :param requirements: list of a tool requirements
    :param hints: list of a tool hints
    :param label: label of a tool
    :param doc: description of a tool
    :param base_command: base command of a tool
    :param arguments: command line bindings which are not directly associated
                      with input parameters
    :param stdin: a path to a file whose contents must be piped into
                  the command's standard input stream
    :param stdout: capture the command's standard output stream to a file
                   written to the designated output directory
    :param stderr: capture the command's standard error stream to a file
                   written to the designated output directory.
    :param success_codes: exit codes that indicate the process completed
                          successfully.
    :param temporary_fail_codes: Exit codes that indicate the process failed
                                 due to a possibly temporary condition
    :param permanent_fail_codes: exit codes that indicate the process failed
                                 due to a permanent logic error
    :param docker: specify a Docker image to retrieve using docker pull
    :param js: include ``InlineJavascriptRequirement``
    :param sh: include ``ShellCommandRequirement``
    :return: typing.Callable[..., CommandLineTool]

    Example:

    .. code-block:: python

       from sbg import cwl

       @cwl.to_tool(
           inputs=dict(x=cwl.Float(), n=cwl.Int()),
           outputs=dict(out=cwl.Float()),
           docker='images.sbgenomics.com/filip_tubic/ubuntu1604py'
       )
       def times_n(x, n=10):
           \"""Returns x * n\"""
           return dict(out=x * n)

       t = times_n()

       print(t.label)  # prints 'to_tool'
       print(t.doc)  # prints 'Returns x * n'
       print(t.inputs)  # prints inputs
       print(t.outputs)  # prints outputs
       print(t.base_command)  # prints [python{major}.{minor}, 'to_tool.py']

    """

    def deco(f):
        @functools.wraps(f)
        def wrapper():
            # monkey patch arguments
            f.to_tool_args = dict(
                inputs=inputs, outputs=outputs, id=id,
                requirements=requirements,
                hints=hints, label=label, doc=doc, base_command=base_command,
                arguments=arguments, stdin=stdin, stdout=stdout, stderr=stderr,
                success_codes=success_codes,
                temporary_fail_codes=temporary_fail_codes,
                permanent_fail_codes=permanent_fail_codes,
                docker=docker, js=js, sh=sh
            )
            t = CommandLineTool(
                inputs=[], outputs=[], id=id, requirements=requirements,
                hints=hints, label=label, doc=doc, base_command=base_command,
                arguments=arguments, stdin=stdin, stdout=stdout,
                stderr=stderr, success_codes=success_codes,
                temporary_fail_codes=temporary_fail_codes,
                permanent_fail_codes=permanent_fail_codes
            )
            if docker:
                t.add_requirement(Docker(docker_pull=docker))
            if js:
                t.add_requirement(InlineJavascript())
            if sh:
                t.add_requirement(ShellCommand())
            return _tool_from(t, f)

        return wrapper

    return deco
