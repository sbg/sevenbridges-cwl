import pytest
from sbg import cwl
from sbg.cwl.v1_0.hints import TypeFactory
from sbg.cwl.v1_0 import (
    CommandLineTool, CommandInput, CommandOutput, Docker, to_tool
)


@pytest.fixture(scope='module')
def inputs():
    return dict(
        input_str=cwl.String(),
        input_int=cwl.Int(),
        input_bool=cwl.Bool(),
        input_float=cwl.Float(),
        input_enum=cwl.Enum(['a', 'b', 'c']),
        input_record=cwl.Record(dict(k1=cwl.String())),
        input_array=cwl.Array(cwl.Int()),
        input_no_type=cwl.Any(),
        input_union=cwl.Union([cwl.Int(), cwl.String()]),
        input_nonreq_primitive=cwl.String(),
        input_nonreq_none=cwl.String(),
        input_nonreq_object=cwl.Enum(['a', 'b', 'c'])
    )


@pytest.fixture(scope='module')
def outputs():
    return dict(
        out_str=cwl.String(),
        out_glob_star=cwl.Array(cwl.File(), glob='*.txt'),
        out_glob=cwl.File(glob="some_name")
    )


@pytest.fixture(scope='function')
def tool(inputs, outputs):
    @to_tool(
        docker="ubuntu:16.04",
        stdout="__stdout__",
        inputs=inputs,
        outputs=outputs
    )
    def dummy(input_str, input_int, input_bool, input_float, input_enum,
              input_record, input_array, input_no_type, input_union,
              input_nonreq_primitive='foo', input_nonreq_none=None,
              input_nonreq_object='b'):
        """Here comes documentation."""
        return dict(
            out_object=input_str
        )

    return dummy()


def test_to_tool_check_instance(tool):
    assert isinstance(tool, CommandLineTool)


def test_to_tool_doc(tool):
    assert tool.doc == 'Here comes documentation.'


def test_to_tool_label(tool):
    assert tool.label == 'dummy'


def test_to_tool_id(tool):
    assert tool.id == 'dummy'


def test_to_tool_check_input_instances(tool):
    for i in tool.inputs:
        assert isinstance(i, CommandInput) is True


def test_to_tool_check_inputs_type(tool, inputs):
    for k, hint in inputs.items():
        input = tool.get_port(k)
        assert input.type == TypeFactory.create(hint, True)


def test_to_tool_check_output_instances(tool):
    for i in tool.outputs:
        assert isinstance(i, CommandOutput) is True


def test_to_tool_check_outputs_type(tool, outputs):
    for k, hint in outputs.items():
        output = tool.get_port(k)
        assert output.type == TypeFactory.create(hint, True)


def test_to_tool_docker(tool):
    d = Docker(docker_pull='ubuntu:16.04')
    assert tool.find_requirement(Docker.class_) == d


def test_to_tool_stdout(tool):
    assert tool.stdout == '__stdout__'
