import os
import re
import pytest
import inspect
import tempfile
from sbg import cwl
import unittest.mock as mock
from sbg.cwl.consts import BASH_LIB
from sbg.cwl.v1_0.hints import TypeFactory
from sbg.cwl.v1_0.requirement import (
    Docker, InitialWorkDir, InlineJavascript, EnvVar, ShellCommand
)


@pytest.fixture(scope='function')
def tool():
    return cwl.CommandLineTool()


@pytest.mark.parametrize('encoded', [True, False])
@pytest.mark.parametrize('postprocess', ['cat aa.txt', 'rm bb.dat'])
@pytest.mark.parametrize('bundle', 'my_bundle')
def test_unarchive_bundle(tool, bundle, postprocess, encoded):
    arg = tool.get_unarchive_argument(
        bundle, encoded=encoded, postprocess=postprocess
    )
    tool.unarchive_bundle(bundle, encoded=encoded, postprocess=postprocess)
    assert tool.arguments[0] == arg


def make_f(t, r=inspect._empty):
    """Argument `t` is type hint for argument `x` of function `f`."""

    def f(x):
        pass

    f.to_tool_args = {
        'inputs': dict(x=t),
        'outputs': r
    }
    return f


@pytest.mark.parametrize('hint', [
    cwl.Int(), cwl.String(), cwl.Float(), cwl.Bool(), cwl.Record(), cwl.Enum()
])
def test_inputs_from_f(tool, hint):
    f = make_f(hint)
    inputs = tool._inputs_from_f(f)
    i = inputs[0]
    assert i['id'] == 'x'
    assert i['type'] == hint


@pytest.mark.parametrize('hint', [
    cwl.Int(), cwl.String(), cwl.Float(), cwl.Bool(), cwl.Record(), cwl.Enum()
])
def test_inputs_from_f_arr(tool, hint):
    f = make_f(cwl.Array(hint))
    inputs = tool._inputs_from_f(f)
    i = inputs[0]
    assert i['id'] == 'x'
    assert type(i['type']) == cwl.Array
    assert i['type'].val == hint


@pytest.mark.parametrize('hint', [
    cwl.Int(), cwl.String(), cwl.Float(), cwl.Bool(), cwl.Record(), cwl.Enum()
])
def test_outputs_from_f(tool, hint):
    f = make_f(int, r={'y': hint})
    outputs = tool._outputs_from_f(f)
    o = outputs[0]
    assert o['id'] == 'y'
    assert o['type'] == hint


@pytest.mark.parametrize('hint', [
    cwl.Int(), cwl.String(), cwl.Float(), cwl.Bool(), cwl.Record(), cwl.Enum()
])
def test_outputs_from_f_arr(tool, hint):
    f = make_f(int, r={'y': cwl.Array(hint)})
    outputs = tool._outputs_from_f(f)
    o = outputs[0]
    assert o['id'] == 'y'
    assert type(o['type']) == cwl.Array
    assert o['type'].val == hint


@pytest.mark.parametrize('hint', [
    cwl.Int(), cwl.String(), cwl.Float(), cwl.Bool(), cwl.Record(), cwl.Enum()
])
def test_set_inputs_from_f(tool, hint):
    f = make_f(hint)
    tool._set_inputs_from(f)
    i = tool.get_port('x')
    assert i.type == TypeFactory.create(hint, True)
    r = tool.find_requirement(InlineJavascript.class_)
    assert r is not None
    r = tool.find_requirement(ShellCommand.class_)
    assert r is not None


@pytest.mark.parametrize('hint', [
    cwl.Int(), cwl.String(), cwl.Float(), cwl.Bool(), cwl.Record(), cwl.Enum()
])
def test_set_outputs_from_f(tool, hint):
    f = make_f(int, r={'y': hint})
    tool._set_outputs_from(f)
    o = tool.get_port('y')
    assert o.type == TypeFactory.create(hint, False)


def test_create_file_from(tool):
    f = make_f(int)
    name = 'foo'
    iwd = 'InitialWorkDirRequirement'
    listing = tool._listing_from_f(f, name)
    tool._create_file_from(f, name)
    assert tool.find_requirement(iwd).listing == listing


@pytest.mark.parametrize('stdout', [None, '__stdout__'])
@pytest.mark.parametrize('name', [None, 'my_script.sh'])
@pytest.mark.parametrize('docker', ['ubuntu1604'])
@pytest.mark.parametrize('doc', ['doc of my tool'])
@pytest.mark.parametrize('label', [None, 'my label'])
@pytest.mark.parametrize('id', [None, 'my_id'])
def test_from_bash_basic(id, label, doc, docker, name, stdout):
    kwargs = {
        'script': 'echo HelloWorld',
        'name': name,
        'docker': docker,
        'doc': doc,
        'label': label,
        'id': id,
        'stdout': stdout
    }

    filtered_kwargs = {
        k: v for k, v in kwargs.items() if v is not None
    }

    tool = cwl.CommandLineTool.from_bash(**filtered_kwargs)

    if id:
        assert tool.id == id
    else:
        if label:
            new_id = '_'.join(map(str.lower, re.findall(r"\w+", label)))
            assert tool.id == new_id
            assert tool.label == label

    assert tool.stdout == stdout
    assert tool.doc == doc
    assert tool.find_requirement(Docker.class_).docker_pull == docker
    assert tool.find_requirement(ShellCommand.class_) is not None
    assert tool.find_requirement(InlineJavascript.class_) is not None
    if not name:
        name = 'script.sh'
    assert cwl.SaveLogs(os.path.basename(name)) in tool.hints
    assert cwl.SaveLogs(os.path.basename(BASH_LIB)) in tool.hints
    if stdout:
        assert cwl.SaveLogs(os.path.basename(stdout)) in tool.hints

    iwd = tool.find_requirement(InitialWorkDir.class_)
    assert iwd is not None
    assert len(iwd.listing) > 0
    found_input_json = False
    for x in iwd.listing:
        if isinstance(x, cwl.Dirent) and x.entryname == 'input.json':
            found_input_json = True
    assert found_input_json is True


@pytest.mark.parametrize('sec', [['.bai', '.bam'], '.txt'])
@pytest.mark.parametrize('req', [True, False])
@pytest.mark.parametrize('hint', [
    cwl.Int, cwl.String, cwl.Float, cwl.Bool, cwl.Enum
])
def test_from_bash_check_io(hint, req, sec):
    h = hint(required=req)
    tool = cwl.CommandLineTool.from_bash(
        'echo $IN',
        inputs={
            'IN': h
        },
        outputs={
            'OUT': h
        },
        secondary_files={'IN': sec}
    )
    envs = tool.find_requirement(EnvVar.class_).env_def
    assert len(envs) == 1
    assert envs[0].env_name == 'IN'
    assert tool.inputs[0].type == TypeFactory.create(h, True)
    assert tool.outputs[0].type == TypeFactory.create(h, False)
    assert tool.inputs[0].secondary_files == sec


@pytest.mark.parametrize('sec', [['.bai', '.bam'], '.txt'])
@pytest.mark.parametrize('req', [True, False])
@pytest.mark.parametrize('hint', [
    cwl.Int(), cwl.String(), cwl.Float(), cwl.Bool(), cwl.Enum()
])
def test_from_bash_check_io_array(hint, req, sec):
    tool = cwl.CommandLineTool.from_bash(
        'echo $IN',
        inputs={
            'IN': cwl.Array(hint, required=req)
        },
        outputs={
            'OUT': cwl.Array(hint, required=req)
        },
        secondary_files={'IN': sec}
    )

    assert tool.inputs[0].type == TypeFactory.create(
        cwl.Array(hint, required=req), True
    )
    assert tool.outputs[0].type == TypeFactory.create(
        cwl.Array(hint, required=req), False
    )
    assert tool.inputs[0].secondary_files == sec


@pytest.mark.parametrize('hints', [
    None, [cwl.SbgFs(True)], [cwl.SaveLogs('aaa'), cwl.SbgFs(True)]
])
@pytest.mark.parametrize('postprocess', ['echo AAA', None])
@pytest.mark.parametrize('name', ['bundle'])
@mock.patch('sbg.cwl.v1_0.cmd.tool.archive')
def test_add_locals(archive_mock, tool, name, postprocess, hints):
    archive_mock.return_value = 'asdfghjk'
    if hints:
        tool.hints = hints
    with tempfile.NamedTemporaryFile(mode='r') as tmp_file:
        locals = [tmp_file.name]
        tool.add_locals(locals, name, postprocess=postprocess)

        archive_mock.assert_called_with(
            list(map(os.path.abspath, locals)),
            encode=True
        )
        assert cwl.SaveLogs(name) in tool.hints
        assert cwl.SaveLogs(os.path.basename(tmp_file.name)) in tool.hints
        if hints:
            for h in hints:
                assert h in tool.hints
