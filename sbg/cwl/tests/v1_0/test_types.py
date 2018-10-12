import pytest
from sbg.cwl.v1_0 import is_primitive, is_number
from sbg.cwl.v1_0.types import File, Directory, to_file_dir_list, Primitive
from sbg.cwl.v1_0.schema import (
    ArrayBase, InputArray, OutputArray, EnumBase, InputEnum, OutputEnum
)


@pytest.mark.parametrize('type', [
    Primitive.BOOLEAN, Primitive.INT, Primitive.LONG, Primitive.FLOAT,
    Primitive.DOUBLE, Primitive.STRING, Primitive.FILE, Primitive.DIRECTORY,
    Primitive.ANY
])
def test_is_primitive(type):
    assert is_primitive(type) is True


@pytest.mark.parametrize('type', [
    Primitive.INT, Primitive.LONG, Primitive.FLOAT, Primitive.DOUBLE
])
def test_is_number(type):
    assert is_number(type) is True


@pytest.mark.parametrize('type', [
    Primitive.BOOLEAN, Primitive.STRING, Primitive.FILE, Primitive.DIRECTORY,
    Primitive.ANY
])
def test_is_not_number(type):
    assert is_number(type) is False


@pytest.mark.parametrize('value', [
    [File(), Directory(), Directory(), File()]
])
def test_to_list_file_dir_instances(value):
    assert to_file_dir_list(value) == value


@pytest.mark.parametrize('value', [
    [
        {'class': 'File', 'path': 'path/to/file'},
        {'class': 'Directory', 'path': 'path/to/dir'}
    ]
])
def test_to_list_file_dir_dicts(value):
    result = to_file_dir_list(value)
    assert isinstance(result[0], File)
    assert result[0].path == 'path/to/file'
    assert result[1].path == 'path/to/dir'


@pytest.mark.parametrize('value', [
    [object()]
])
def test_to_list_file_dir_type_error(value):
    with pytest.raises(TypeError):
        to_file_dir_list(value)


@pytest.mark.parametrize('value', [
    [{'class': 'A'}, {'class': 'B'}]
])
def test_to_list_file_dir_value_error(value):
    with pytest.raises(ValueError):
        to_file_dir_list(value)


@pytest.mark.parametrize('items', [
    Primitive.FILE, InputArray(Primitive.FILE),
    InputArray(InputArray(Primitive.FILE))
])
def test_input_array_with_items(items):
    input_array = InputArray(items)
    assert type(input_array.items_) == type(items)
    assert input_array['type'] == ArrayBase.type


@pytest.mark.parametrize('items', [
    Primitive.FILE, OutputArray(Primitive.FILE),
    OutputArray(OutputArray(Primitive.FILE))
])
def test_output_array_with_items(items):
    output_array = OutputArray(items)
    assert type(output_array.items_) == type(items)
    assert output_array['type'] == ArrayBase.type


@pytest.mark.parametrize('input_array', [
    InputArray(Primitive.FILE), InputArray(InputArray(Primitive.FILE))
])
def test_input_array_from_dict(input_array):
    raw_dict = input_array.to_dict()
    input_array = InputArray(**raw_dict)
    assert input_array.type == raw_dict['type']


@pytest.mark.parametrize('output_array', [
    OutputArray(Primitive.FILE), OutputArray(OutputArray(Primitive.FILE))
])
def test_output_array_from_dict(output_array):
    raw_dict = output_array.to_dict()
    output_array = OutputArray(**raw_dict)
    assert output_array.type == raw_dict['type']


def test_input_enum():
    symbols = ['a', 'b', 'c']
    input_enum = InputEnum(symbols)
    assert input_enum.symbols == symbols
    assert input_enum['type'] == EnumBase.type


def test_output_enum():
    symbols = ['a', 'b', 'c']
    output_enum = OutputEnum(symbols)
    assert output_enum.symbols == symbols
    assert output_enum['type'] == EnumBase.type


def test_input_enum_from_dict():
    symbols = ['a', 'b', 'c']
    raw_dict = InputEnum(symbols).to_dict()
    input_enum = InputEnum(**raw_dict)
    assert input_enum.type == raw_dict['type']
    assert input_enum.symbols == raw_dict['symbols']


def test_output_enum_from_dict():
    symbols = ['a', 'b', 'c']
    raw_dict = OutputEnum(symbols).to_dict()
    output_enum = OutputEnum(**raw_dict)
    assert output_enum.type == raw_dict['type']
    assert output_enum.symbols == raw_dict['symbols']
