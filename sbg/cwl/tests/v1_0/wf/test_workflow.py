import pytest
from sbg import cwl
from functools import partial

from sbg.cwl.v1_0.hints import TypeFactory
from sbg.cwl.v1_0.schema import set_required
from sbg.cwl.v1_0 import (
    CommandLineTool, Workflow, InitialWorkDir, Dirent, Primitive,
    InlineJavascript, Resource, ShellCommand, EnvVar, EnvironmentDef,
    Software, SoftwarePackage, SchemaDef, Docker, InputEnum, StepOutput,
    StepInput, Step, WorkflowOutput, WorkflowInput, StepInputExpression,
    ScatterFeature, MultipleInputFeature, SubworkflowFeature, InputArray,
    OutputArray, ScatterMethod, is_primitive
)


@pytest.fixture(scope='function')
def wf():
    return Workflow()


def test_get_step(wf):
    t1 = CommandLineTool(id='t1')
    t2 = CommandLineTool(id='t2')
    wf.add_step(t1)
    wf.add_step(t2)
    assert wf.get_step('t1').run == t1
    assert wf.get_step('t2').run == t2


@pytest.mark.parametrize('req', [
    InlineJavascript(),
    SchemaDef([InputEnum(['a', 'b', 'c'])]),
    Software([SoftwarePackage('samtools')]),
    ShellCommand(),
    Resource(),
    Docker(docker_pull='something'), InlineJavascript(),
    EnvVar(EnvironmentDef('foo', 'bar')),
    InitialWorkDir([Dirent('hello world', 'foo.txt')]),
    EnvVar(EnvironmentDef('foo', 'bar')),
    StepInputExpression(),
    ScatterFeature(),
    MultipleInputFeature(),
    SubworkflowFeature()
])
def test_add_requirement(wf, req):
    wf.add_requirement(req)
    assert wf.requirements[0] == req


def test_add_step(wf):
    t1 = CommandLineTool(id='t1')
    t2 = CommandLineTool(id='t2')
    t3 = Workflow()
    wf.add_step(t1)
    wf.add_step(t2)
    wf.add_step(t3)
    assert wf.steps[0] == Step(t1.id, [], [], t1)
    assert wf.steps[1] == Step(t2.id, [], [], t2)
    assert wf.steps[2] == Step(t3.id, [], [], t3)


@pytest.mark.parametrize('required', [True, False])
@pytest.mark.parametrize('hint', [
    cwl.String, cwl.Int, cwl.Float, cwl.Bool, cwl.File, cwl.Dir,
    partial(cwl.Enum, val=['a', 'b', 'c']),
    partial(cwl.Array, val=cwl.Int()),
    partial(cwl.Record, val={'y': cwl.Int()})
])
def test_scatter_single_check_input(wf, hint, required):
    t1 = CommandLineTool(id='t1')
    ihint = hint(required=required)
    t = TypeFactory.create(ihint, True)

    t1.add_input(ihint, 'input')
    step1 = wf.add_step(t1, expose=['input'])
    wf.scatter(step1, ['input'], None)
    assert isinstance(wf.inputs[0].type, InputArray)
    if is_primitive(t) and not ihint.required:
        t = [Primitive.NULL, t.rstrip('?')]
    assert wf.inputs[0].type.items_ == t


@pytest.mark.parametrize('method', [
    ScatterMethod.FLAT_CROSSPRODUCT, ScatterMethod.NESTED_CROSSPRODUCT,
    ScatterMethod.DOTPRODUCT
])
@pytest.mark.parametrize('req', [True, False])
@pytest.mark.parametrize('hint', [
    cwl.String, cwl.Int, cwl.Float, cwl.Bool, cwl.File, cwl.Dir,
    partial(cwl.Enum, val=['a', 'b', 'c']),
    partial(cwl.Array, val=cwl.Int()),
    partial(cwl.Record, val={'y': cwl.Int()})
])
def test_scatter_multi_check_input(wf, hint, req, method):
    tool = CommandLineTool(id='t')
    h = hint(required=req)
    hint_type = TypeFactory.create(h, True)

    inputs = [
        tool.add_input(h, 'input1'),
        tool.add_input(h, 'input2')
    ]
    step = wf.add_step(tool, expose=['input1', 'input2'])
    wf.scatter(step, ['input1', 'input2'], method)

    if is_primitive(hint_type) and not h.required:
        hint_type = [Primitive.NULL, hint_type.rstrip('?')]

    for i in inputs:
        wfi = wf.get_port(i.id)
        assert isinstance(wfi.type, InputArray)
        assert wfi.type.items_ == hint_type


@pytest.mark.parametrize('req', [True, False])
@pytest.mark.parametrize('hint', [
    cwl.String, cwl.Int, cwl.Float, cwl.Bool, cwl.File, cwl.Dir,
    partial(cwl.Enum, val=['a', 'b', 'c']),
    partial(cwl.Array, val=cwl.Int()),
    partial(cwl.Record, val={'y': cwl.Int()})
])
def test_scatter_single_check_output(wf, hint, req):
    tool = CommandLineTool(id='t')
    h = hint(required=req)

    tool.add_input(h, 'input')
    tool.add_output(h, 'output')

    step = wf.add_step(tool, expose=['output'])

    wf.scatter(step, ['input'], None)
    if req:
        assert isinstance(wf.outputs[0].type, OutputArray)
    else:
        assert Primitive.NULL in wf.outputs[0].type
        wf.outputs[0].type.remove(Primitive.NULL)
        assert len(wf.outputs[0].type) == 1
        assert isinstance(wf.outputs[0].type[0], OutputArray)
        h.required = True
        assert wf.outputs[0].type[0].items_ == TypeFactory.create(h, False)


@pytest.mark.parametrize('method', [
    ScatterMethod.FLAT_CROSSPRODUCT, ScatterMethod.NESTED_CROSSPRODUCT,
    ScatterMethod.DOTPRODUCT
])
@pytest.mark.parametrize('req', [True, False])
@pytest.mark.parametrize('hint', [
    cwl.String, cwl.Int, cwl.Float, cwl.Bool, cwl.File, cwl.Dir,
    partial(cwl.Enum, val=['a', 'b', 'c']),
    partial(cwl.Array, val=cwl.Int()),
    partial(cwl.Record, val={'y': cwl.Int()})
])
def test_scatter_multi_check_output(wf, hint, req, method):
    tool = CommandLineTool(id='t')
    h = hint(required=req)

    inputs = [
        tool.add_input(h, 'input1'),
        tool.add_input(h, 'input2'),
        tool.add_input(h, 'input3')
    ]
    outputs = [
        tool.add_output(h, 'output1'),
        tool.add_output(h, 'output2')
    ]
    scatter = [i.id for i in inputs]
    step = wf.add_step(tool, expose=scatter + [o.id for o in outputs])
    wf.scatter(step, scatter, method)

    # number of iterations
    n = len(scatter) if method == ScatterMethod.NESTED_CROSSPRODUCT else 1

    for o in outputs:
        wfo = wf.get_port(o.id)
        if req:
            parent = wfo.type
            for _ in range(n):
                assert isinstance(parent, OutputArray)
                parent = parent.items_
        else:
            assert Primitive.NULL in wfo.type
            wfo.type.remove(Primitive.NULL)
            assert len(wfo.type) == 1
            parent = wfo.type[0]
            for _ in range(n):
                assert isinstance(parent, OutputArray)
                parent = parent.items_

        h.required = True
        assert parent == TypeFactory.create(h, False)


def test_expose(wf):
    t = CommandLineTool(id='test')
    t.add_input(cwl.Int(default=10, required=True), id='x')
    t.add_input(cwl.String(), id='y')
    t.add_output(cwl.File(glob='something', required=True), id='out')
    wf.add_step(t, expose=['x', 'out'])

    assert wf.inputs == [WorkflowInput(id='x', label='x', type=Primitive.INT)]
    assert wf.outputs == [WorkflowOutput(
        id='out', label='out', type=Primitive.FILE, output_source='test/out')
    ]


def test_expose_except(wf):
    t = CommandLineTool(id='test')
    t.add_input(cwl.Int(default=10, required=True), id='x')
    t.add_input(cwl.String(), id='y')
    t.add_output(cwl.File(glob='something', required=True), id='out')
    wf.add_step(t, expose_except=['y', 'out'])
    assert wf.inputs == [WorkflowInput(id='x', label='x', type=Primitive.INT)]
    assert wf.outputs == []


def test_add_connection_inner_nodes(wf):
    t1 = CommandLineTool(id='t1')
    t2 = CommandLineTool(id='t2')

    t1.add_input(cwl.String(), 'input')
    t1.add_output(cwl.String(), 'output')

    t2.add_input(cwl.String(), 'input')
    t2.add_output(cwl.String(), 'output')

    wf.add_step(t1, expose=[])
    wf.add_step(t2, expose=[])

    wf.add_connection('t1.output', 't2.input')

    assert wf.steps[0].out == [StepOutput('output')]
    assert wf.steps[1].in_ == [StepInput('input', source='t1/output')]


def test_add_connection_wf_input(wf):
    wf.add_input(cwl.String(), 'input_str')

    t1 = CommandLineTool(id='t1')
    t1.add_input(cwl.String(), 'input_str')

    wf.add_step(t1, expose=[])

    wf.add_connection('input_str', 't1.input_str')

    assert wf.steps[0].in_ == [StepInput('input_str', source='input_str')]


def test_add_connection_wf_output(wf):
    wf.add_output(cwl.String(), 'output_str')

    t1 = CommandLineTool(id='t1')
    t1.add_output(cwl.String(), 'output_str')

    wf.add_step(t1, expose=[])

    wf.add_connection('t1.output_str', 'output_str')

    assert wf.outputs[0] == WorkflowOutput(
        id='output_str',
        output_source='t1/output_str',
        type=set_required(Primitive.STRING, False)
    )


def test_auto_expose_all(wf):
    t = CommandLineTool(id='t')

    input = t.add_input(cwl.String(), 'input')
    output = t.add_output(cwl.String(), 'output')

    wf.add_step(t)

    assert wf.inputs == [
        WorkflowInput(
            id='input', label='input', type=Workflow.set_required(
                Primitive.STRING, False
            )
        )
    ]

    assert wf.outputs == [
        WorkflowOutput(
            id='output', label='output',
            output_source='{}/{}'.format(t.id, output.id),
            type=Workflow.set_required(
                Primitive.STRING, False
            )
        )
    ]

    assert wf.steps[0] == Step(
        id=t.id,
        in_=[StepInput(input.id, source=input.id)],
        out=[StepOutput(output.id)],
        run=t
    )


@pytest.mark.parametrize('scatter', [
    ['input1'], ['input1', 'input2'], ['input1', 'input2', 'input3'],
])
@pytest.mark.parametrize('req', [True, False])
@pytest.mark.parametrize('hint', [
    cwl.String, cwl.Int, cwl.Float, cwl.Bool, cwl.File, cwl.Dir,
    partial(cwl.Enum, val=['a', 'b', 'c']),
    partial(cwl.Array, val=cwl.Int()),
    partial(cwl.Record, val={'y': cwl.Int()})
])
def test_is_scattered(wf, hint, req, scatter):
    tool = CommandLineTool(id='t')
    h = hint(required=req)

    tool.add_input(h, 'input1')
    tool.add_input(h, 'input2')
    tool.add_input(h, 'input3')

    step = wf.add_step(tool, scatter=scatter)

    for k in scatter:
        assert step.is_scattered(k) is True
