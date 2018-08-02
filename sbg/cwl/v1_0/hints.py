import inspect
import functools
from sbg.cwl.v1_0.types import Primitive, is_primitive
from sbg.cwl.v1_0.schema import (
    EnumBase, InputEnum, OutputEnum, RecordBase, InputRecord, OutputRecord,
    ArrayBase, InputArray, OutputArray, InputRecordField, OutputRecordField,
    UnionBase, set_required
)


class Empty(inspect._empty):
    pass


def is_empty(x):
    return inspect.isclass(x) and issubclass(x, inspect._empty)


class Hint(object):
    def __init__(self, val=None, default=Empty, glob=None, required=False,
                 label=None, doc=None, secondary_files=None):
        self._default = default
        self._val = val
        self._glob = glob
        self._required = required
        self._label = label
        self._doc = doc
        self._secondary_files = secondary_files

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, value):
        self._default = value

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, value):
        self._val = value

    @property
    def glob(self):
        return self._glob

    @glob.setter
    def glob(self, value):
        self._glob = value

    @property
    def required(self):
        return self._required

    @required.setter
    def required(self, value):
        self._required = value

    @property
    def type(self):
        raise NotImplementedError()

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value

    @property
    def doc(self):
        return self._doc

    @doc.setter
    def doc(self, value):
        self._doc = value

    @property
    def secondary_files(self):
        return self._secondary_files

    @secondary_files.setter
    def secondary_files(self, value):
        self._secondary_files = value


class Union(Hint):
    @property
    def type(self):
        return UnionBase


class Int(Hint):
    @property
    def type(self):
        return Primitive.INT


class Float(Hint):
    @property
    def type(self):
        return Primitive.FLOAT


class String(Hint):
    @property
    def type(self):
        return Primitive.STRING


class Bool(Hint):
    @property
    def type(self):
        return Primitive.BOOLEAN


class File(Hint):
    @property
    def type(self):
        return Primitive.FILE


class Dir(Hint):
    @property
    def type(self):
        return Primitive.DIRECTORY


class Any(Hint):
    @property
    def type(self):
        return Primitive.ANY


class Enum(Hint):
    @property
    def type(self):
        return EnumBase


class Record(Hint):
    @property
    def type(self):
        return RecordBase


class Array(Hint):
    @property
    def type(self):
        return ArrayBase


class TypeFactory:
    """Factory for creating concrete types from type hints."""

    @staticmethod
    def _to_type(hint, in_):
        me = dict([(True, InputEnum), (False, OutputEnum)])
        ma = dict([(True, InputArray), (False, OutputArray)])
        mr = dict([(True, InputRecord), (False, OutputRecord)])
        mf = dict([(True, InputRecordField), (False, OutputRecordField)])

        t = hint.type
        if is_primitive(t):
            return t
        else:
            if t == EnumBase:
                return me[in_](hint.val)
            elif t == ArrayBase:
                return ma[in_](TypeFactory._to_type(hint.val, in_))
            elif t == UnionBase:
                return list(map(
                    functools.partial(TypeFactory._to_type, in_=in_),
                    hint.val
                ))
            else:  # record
                if hint.val:
                    f = [
                        mf[in_](name=k, type=TypeFactory._to_type(v, in_))
                        for k, v in hint.val.items()
                    ]
                else:
                    f = []
                return mr[in_](fields=f)

    @staticmethod
    def create(hint, in_):
        """
        if ``input is True`` returns an instance of input class
        else returns an instance of output class

        :param hint: an instance of Hint class
        :param in_: bool (True for inputs, False for outputs)
        :return: type for cmd input/output
        """

        return set_required(TypeFactory._to_type(hint, in_), hint.required)
