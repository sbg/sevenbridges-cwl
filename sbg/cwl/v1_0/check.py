from sbg.cwl.v1_0.base import salad
from sbg.cwl.v1_0.util import is_instance_both


@salad
def to_any(value):
    return value


@salad
def to_str_int(value):
    if value is not None:
        if isinstance(value, (str, int)):
            return value
        else:
            raise TypeError('Expected str|int, got {}'.format(type(value)))


@salad
def to_bool(value):
    if value is not None:
        if isinstance(value, bool):
            return value
        else:
            raise TypeError('Expected bool, got: {}'.format(type(value)))


@salad
def to_str(value):
    if value is not None:
        if isinstance(value, str):
            return value
        else:
            raise TypeError('Expected str, got: {}'.format(type(value)))


@salad
def to_int(value):
    if value is not None:
        if isinstance(value, int):
            return value
        else:
            raise TypeError('Expected int, got: {}'.format(type(value)))


@salad
def to_list(value):
    if value is not None:
        if isinstance(value, list):
            return value
        else:
            raise TypeError('Expected list, got {}'.format(type(value)))


@salad
def to_slist(obj):
    if obj is not None:
        if isinstance(obj, list):
            return list(map(to_str, obj))
        else:
            raise TypeError('Expected list[str], got: {}'.format(type(obj)))


@salad
def to_ilist(obj):
    if obj is not None:
        if isinstance(obj, list):
            return list(map(to_int, obj))
        else:
            raise TypeError('Expected list[int], got: {}'.format(type(obj)))


@salad
def to_str_slist(value):
    if value is not None:
        if is_instance_both(value, str):
            return value
        else:
            raise TypeError(
                "Expected str|list[str], got: {}".format(type(value))
            )
