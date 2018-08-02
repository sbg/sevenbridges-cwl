import pytest
from sbg.cwl.v1_0 import Primitive, is_primitive, is_number
from sbg.cwl.v1_0.types import File, Directory, to_file_dir_list


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
