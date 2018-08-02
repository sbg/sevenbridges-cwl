import pytest
import base64

from sbg.cwl.v1_0.schema import set_required, OutputArray, InputArray
from sbg import cwl
from sbg.cwl.consts import SBG_NAMESPACE
from sbg.cwl.v1_0 import (
    CommandLineTool, Workflow, InitialWorkDir, Dirent, Primitive,
    InlineJavascript, Resource, ShellCommand, EnvVar, EnvironmentDef,
    Software, SoftwarePackage, SchemaDef, Docker, InputEnum, App
)
from sbg.cwl.v1_0.app import INHERIT_SINGLE, INHERIT_MULTI
from sbg.cwl.v1_0.hints import TypeFactory


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
def test_add_hints(cls):
    obj = cls()
    hints = [{'class': c} for c in ('Hint1', 'Hint2', 'Hint3')]
    obj.add_hints(*hints)
    assert obj.hints == hints


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
def test_add_input_json(cls):
    obj = cls()
    entryname = 'input.json'
    entry = '$(JSON.stringify(inputs, null, 2))'

    obj.add_input_json()
    file = obj.create_file(
        entry, entryname=entryname, encode=False
    )
    assert obj.requirements[0].listing[0] == file


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
@pytest.mark.parametrize('req', [
    InlineJavascript(),
    SchemaDef([InputEnum(['a', 'b', 'c'])]),
    Software([SoftwarePackage('samtools')]),
    ShellCommand(),
    Resource(),
    Docker(docker_pull='something'), InlineJavascript(),
    EnvVar(EnvironmentDef('foo', 'bar')),
    InitialWorkDir([Dirent('hello world', 'foo.txt')]),
    EnvVar(EnvironmentDef('foo', 'bar'))
])
def test_find_requirement(req, cls):
    obj = cls()
    obj.add_requirement(req)
    assert obj.find_requirement(req.class_) == req


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
@pytest.mark.parametrize('type', [
    cwl.String(), cwl.Int(), cwl.Float(), cwl.Bool(), cwl.Record(), cwl.Enum(),
    cwl.Array(cwl.Int())
])
def test_get_port(type, cls):
    obj = cls()
    i = obj.add_input(type, id='in')
    o = obj.add_output(type, id='out')

    assert obj.get_port('in') == i
    assert obj.get_port('out') == o


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
@pytest.mark.parametrize('type', [
    cwl.String(), cwl.Int(), cwl.Float(), cwl.Bool(), cwl.Record(), cwl.Enum(),
    cwl.Array(cwl.Int())
])
def test_get_input(type, cls):
    obj = cls()
    i = obj.add_input(type, id='in')
    assert obj.inputs[0] == i


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
@pytest.mark.parametrize('type', [
    cwl.String(), cwl.Int(), cwl.Float(), cwl.Bool(), cwl.Record(), cwl.Enum(),
    cwl.Array(cwl.Int())
])
def test_get_output(type, cls):
    obj = cls()
    o = obj.add_output(type, id='out')
    assert obj.outputs[0] == o


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
@pytest.mark.parametrize('encode', [True, False])
@pytest.mark.parametrize('writable', [True, False])
@pytest.mark.parametrize('entry, entryname', [('fooo', 'xyz.txt')])
def test_create_file(cls, entry, entryname, writable, encode):
    obj = cls()
    f = obj.create_file(
        entry=entry, entryname=entryname, writable=writable, encode=encode
    )
    if encode:
        entry = base64.b64encode(entry.encode('utf-8')).decode("utf-8")

    assert f == Dirent(
        entry=entry, entryname=entryname, writable=writable
    )


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
def test_add_file(cls):
    obj = cls()
    obj.add_file('Some text.', 'file.txt')
    found = False
    for r in obj.requirements:
        if isinstance(r, InitialWorkDir):
            found = True
            x = r.listing[0]
            assert isinstance(x, Dirent)
            break
    assert found is True


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
def test_stage_input(cls):
    obj = cls()
    id = 'dummy'
    obj.stage_input(id)
    stage = '$(inputs.{})'.format(id)
    assert obj.requirements[0].listing[0] == stage


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
@pytest.mark.parametrize('secondary', ['.bai', '^.bam', ['.bai', '^.bam']])
def test_set_secondary_files(cls, secondary):
    obj = cls()
    i = obj.add_input(cwl.File(), id='in')
    o = obj.add_output(cwl.File(), id='out')
    obj.set_secondary_files('in', secondary)
    obj.set_secondary_files('out', secondary)
    assert i.secondary_files == secondary
    assert o.secondary_files == secondary


@pytest.mark.parametrize('single', [True, False])
def test_get_inherit_expr(single):
    kw = {'preprocess': '', 'input': 'something'}
    if single:
        assert App._get_inherit_expr(single, **kw) == INHERIT_SINGLE.format(
            **kw
        )
    else:
        assert App._get_inherit_expr(single, **kw) == INHERIT_MULTI.format(
            **kw
        )


@pytest.mark.parametrize('t', [
    'File[]?', 'File[]',
    InputArray(Primitive.FILE), OutputArray(Primitive.FILE),
    [Primitive.NULL, InputArray(Primitive.FILE)],
    [Primitive.NULL, OutputArray(Primitive.FILE)]
])
def test_is_file_array(t):
    assert App._is_file_array(t) is True


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
def test_add_sbg_namespace(cls):
    obj = cls()
    cwl.App.add_sbg_namespace(obj)
    assert obj['$namespaces'] == {'sbg': SBG_NAMESPACE}


@pytest.mark.parametrize('required', [True, False])
@pytest.mark.parametrize('primitive', [
    Primitive.BOOLEAN, Primitive.INT, Primitive.LONG, Primitive.FLOAT,
    Primitive.DOUBLE, Primitive.STRING, Primitive.FILE, Primitive.DIRECTORY,
    Primitive.ANY
])
def test_set_required(primitive, required):
    val = "{}{}".format(primitive, '?' if not required else '')
    assert set_required(primitive, required) == val


@pytest.mark.parametrize('type', [
    'type?', [Primitive.NULL, 'type']
])
def test_is_required_false(type):
    assert App.is_required(type) is False


@pytest.mark.parametrize('type', [
    'type', ['type'], {'a': 'b'}, [{'a': 'b'}]
])
def test_is_required_true(type):
    assert App.is_required(type) is True


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
def test_add_expression_lib(cls):
    obj = cls()
    lib = 'function f(){ }'
    obj.add_expression_lib(lib)
    found = False
    for r in obj.requirements:
        if isinstance(r, InlineJavascript):
            assert r.expression_lib[0] == lib
            found = True
            break
    assert found is True


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
def test_add_env_var(cls):
    obj = cls()
    obj.add_env_var(env_name='RABIX', env_value='rabix')
    assert obj.requirements[0] == EnvVar([EnvironmentDef('RABIX', 'rabix')])


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
def test_add_in_workdir(cls):
    obj = cls()
    stage = '$(inputs.dummy)'
    obj.add_in_workdir(stage)
    assert obj.requirements[0] == InitialWorkDir([stage])


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
@pytest.mark.parametrize('req', [
    InlineJavascript(),
    SchemaDef([InputEnum(['a', 'b', 'c'])]),
    Software([SoftwarePackage('samtools')]),
    ShellCommand(),
    Resource(),
    Docker(docker_pull='something'), InlineJavascript(),
    EnvVar(EnvironmentDef('foo', 'bar')),
    InitialWorkDir([Dirent('hello world', 'foo.txt')]),
    EnvVar(EnvironmentDef('foo', 'bar'))
])
def test_add_requirement(cls, req):
    obj = cls()
    obj.add_requirement(req)
    assert obj.requirements[0] == req


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
@pytest.mark.parametrize('required', [True, False])
@pytest.mark.parametrize('hint', [
    cwl.String, cwl.Int, cwl.Float, cwl.Bool, cwl.Record, cwl.Enum, cwl.File,
    cwl.Dir
])
def test_add_input(cls, hint, required):
    obj = cls()
    t = hint(required=required)
    i = obj.add_input(t)
    assert i.type == TypeFactory.create(t, True)


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
@pytest.mark.parametrize('required', [True, False])
@pytest.mark.parametrize('hint', [
    cwl.String, cwl.Int, cwl.Float, cwl.Bool, cwl.Record, cwl.Enum, cwl.File,
    cwl.Dir
])
def test_add_input_arr(cls, hint, required):
    obj = cls()
    t = cwl.Array(hint(), required=required)
    i = obj.add_input(t)
    assert i.type == TypeFactory.create(t, True)


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
@pytest.mark.parametrize('required', [True, False])
@pytest.mark.parametrize('hint', [
    cwl.String, cwl.Int, cwl.Float, cwl.Bool, cwl.Record, cwl.Enum, cwl.File,
    cwl.Dir
])
def test_add_output(cls, hint, required):
    obj = cls()
    t = hint(required=required)
    o = obj.add_input(t)
    assert o.type == TypeFactory.create(t, True)


@pytest.mark.parametrize('cls', [CommandLineTool, Workflow])
@pytest.mark.parametrize('required', [True, False])
@pytest.mark.parametrize('hint', [
    cwl.String, cwl.Int, cwl.Float, cwl.Bool, cwl.Record, cwl.Enum, cwl.File,
    cwl.Dir
])
def test_add_output_arr(cls, hint, required):
    obj = cls()
    t = cwl.Array(hint(), required=required)
    o = obj.add_output(t)
    assert o.type == TypeFactory.create(t, False)
