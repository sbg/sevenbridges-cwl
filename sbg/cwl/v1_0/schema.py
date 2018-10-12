from sbg.cwl.v1_0.base import Cwl, salad
from sbg.cwl.v1_0.types import Primitive
from sbg.cwl.v1_0.util import (
    is_instance_all, is_instance_both
)
from sbg.cwl.v1_0.check import (
    to_int, to_str, to_bool, to_slist, to_str_slist
)


def input_schema_item(value):
    @salad
    def set_item(value):
        if isinstance(value, dict):
            if 'type' in value:
                if value['type'] == 'enum':
                    return InputEnum(**value)
                elif value['type'] == 'record':
                    return InputRecord(**value)
                elif value['type'] == 'array':
                    return InputArray(**value)
                else:
                    raise ValueError("Found item: {}".format(value))
            else:
                raise ValueError("Found item: {}".format(value))
        elif isinstance(value, str):
            return value
        else:
            raise NotImplementedError("{}".format(value))

    if value is not None:
        if is_instance_all(
                value, InputRecord, InputEnum, InputArray, str
        ) or isinstance(
            value, (InputRecord, InputEnum, InputArray, str)
        ):
            return value
        elif isinstance(value, list):
            return list(map(set_item, value))
        elif isinstance(value, dict):
            return set_item(value)
        else:
            raise TypeError('Expected <input type>, got:{}'.format(
                type(value))
            )


@salad
def input_binding(value):
    if value is not None:
        if isinstance(value, InputBinding):
            return value
        elif isinstance(value, dict):
            return InputBinding(**value)
        else:
            raise TypeError(
                'Expected InputBinding, got: {}'.format(type(value))
            )


@salad
def output_schema_item(value):
    @salad
    def set_item(value):
        if isinstance(value, dict):
            if 'type' in value:
                if value['type'] == 'enum':
                    return OutputEnum(**value)
                elif value['type'] == 'record':
                    return OutputRecord(**value)
                elif value['type'] == 'array':
                    return OutputArray(**value)
                else:
                    raise ValueError("Found item: {}".format(value))
            else:
                raise ValueError("Found item: {}".format(value))
        elif isinstance(value, str):
            return value
        else:
            raise NotImplementedError("{}".format(value))

    if value is not None:
        if is_instance_both(
                value, OutputEnum, OutputRecord, OutputArray, str
        ):
            return value
        elif isinstance(value, list):
            return list(map(set_item, value))
        elif isinstance(value, dict):
            return set_item(value)
        else:
            raise TypeError('Expected <out type>, got:{}'.format(type(value)))


@salad
def output_binding(value):
    if value is not None:
        if isinstance(value, OutputBinding):
            return value
        elif isinstance(value, dict):
            return OutputBinding(**value)
        else:
            raise TypeError(
                "Expected OutputBinding, got: {}".format(type(value))
            )


class InputBinding(Cwl):
    """
    When listed under inputBinding in the input schema, the term "value" refers
    to the the corresponding value in the input object. For binding objects
    listed in CommandLineTool.arguments, the term "value" refers to the
    effective value after evaluating valueFrom.

    The binding behavior when building the command line depends on the data
    type of the value. If there is a mismatch between the type described by the
    input schema and the effective value, such as resulting from an expression
    evaluation, an implementation must use the data type of the effective
    value.

     - string: Add prefix and the string to the command line.
     - number: Add prefix and decimal representation to command line.
     - boolean: If true, add prefix to the command line. If false, add nothing.
     - File: Add prefix and the value of File.path to the command line.
     - array: If itemSeparator is specified, add prefix and the join the array
       into a single string with itemSeparator separating the items. Otherwise
       first add prefix, then recursively process individual elements.
     - object: Add prefix only, and recursively add object fields for which
       inputBinding is specified.
     - null: Add nothing.

    """

    def __init__(self, load_contents=None, position=None, prefix=None,
                 separate=None, item_separator=None, value_from=None,
                 shell_quote=None):
        super(InputBinding, self).__init__()
        self.load_contents = load_contents
        self.position = position
        self.prefix = prefix
        self.separate = separate
        self.item_separator = item_separator
        self.value_from = value_from
        self.shell_quote = shell_quote

    @property
    def load_contents(self):
        """
        Only valid when type File or is an array of items File.Read up to the
        first 64 KiB of text from the file and place it in the "contents" field
        of the file object for use by expressions.
        """
        return self.get('loadContents')

    @load_contents.setter
    def load_contents(self, value):
        self['loadContents'] = to_bool(value)

    @property
    def position(self):
        """
        The sorting key. Default position is 0.
        """
        return self.get('position')

    @position.setter
    def position(self, value):
        self['position'] = to_int(value)

    @property
    def prefix(self):
        """
        Command line prefix to add before the value.
        """
        return self.get('prefix')

    @prefix.setter
    def prefix(self, value):
        self['prefix'] = to_str(value)

    @property
    def separate(self):
        """
        If true (default), then the prefix and value must be added as separate
        command line arguments; if false, prefix and value must be concatenated
        into a single command line argument.
        """
        return self.get('separate')

    @separate.setter
    def separate(self, value):
        self['separate'] = to_bool(value)

    @property
    def item_separator(self):
        """
        Join the array elements into a single string with the elements
        separated by by itemSeparator.
        """
        return self.get('itemSeparator')

    @item_separator.setter
    def item_separator(self, value):
        self['itemSeparator'] = to_str(value)

    @property
    def value_from(self):
        """
        If valueFrom is a constant string value, use this as the value and
        apply the binding rules above.

        If valueFrom is an expression, evaluate the expression to yield the
        actual value to use to build the command line and apply the binding
        rules above. If the inputBinding is associated with an input parameter,
        the value of self in the expression will be the value of the input
        parameter. Input parameter defaults (as specified by the InputParameter
        default field) must be applied before evaluating the expression.

        When a binding is part of the CommandLineTool.arguments field, the
        valueFrom field is required.
        """
        return self.get('valueFrom')

    @value_from.setter
    def value_from(self, value):
        self['valueFrom'] = to_str(value)

    @property
    def shell_quote(self):
        """
        If ShellCommandRequirement is in the requirement for the current
        command, this controls whether the value is quoted on the command line
        (default is true). Use shellQuote: false to inject metacharacters for
        operations such as pipes.

        If shellQuote is true or not provided, the implementation must not
        permit interpretation of any shell metacharacters or directives.
        """
        return self.get('shellQuote')

    @shell_quote.setter
    def shell_quote(self, value):
        self['shellQuote'] = to_bool(value)


class OutputBinding(Cwl):
    """
    Describes how to generate an output parameter based on the files produced
    by a CommandLineTool.

    The output parameter value is generated by applying these operations in the
    following order:

    - glob
    - loadContents
    - outputEval
    - secondaryFiles
    """

    def __init__(self, glob=None, load_contents=None, output_eval=None):
        super(OutputBinding, self).__init__()
        self.glob = glob
        self.load_contents = load_contents
        self.output_eval = output_eval

    @property
    def glob(self):
        """
        Find files relative to the output directory, using POSIX glob(3)
        pathname matching. If an array is provided, find files that match
        any pattern in the array. If an expression is provided, the expression
        must return a string or an array of strings, which will then be
        evaluated as one or more glob patterns. Must only match and return
        files which actually exist.
        """
        return self.get('glob')

    @glob.setter
    def glob(self, value):
        self['glob'] = to_str_slist(value)

    @property
    def load_contents(self):
        """
        For each file matched in glob, read up to the first 64 KiB of text from
        the file and place it in the contents field of the file object for
        manipulation by outputEval.
        """
        return self.get('loadContents')

    @load_contents.setter
    def load_contents(self, value):
        self['loadContents'] = to_bool(value)

    @property
    def output_eval(self):
        """
        Evaluate an expression to generate the output value. If glob was
        specified, the value of self must be an array containing file objects
        that were matched. If no files were matched, self must be a zero length
        array; if a single file was matched, the value of self is an array of a
        single element. Additionally, if loadContents is true, the File objects
        must include up to the first 64 KiB of file contents in the contents
        field.
        """
        return self.get('outputEval')

    @output_eval.setter
    def output_eval(self, value):
        self['outputEval'] = to_str(value)


class SchemaBase(Cwl):
    pass


class UnionBase(SchemaBase):
    pass


class RecordBase(SchemaBase):
    type = 'record'

    def __init__(self, label=None, fields=None, type='record'):
        super(RecordBase, self).__init__()
        assert type == self.type
        self['type'] = self.type
        self.label = label
        self.fields = fields

    @property
    def fields(self):
        """
        Defines the fields of the record.
        """
        return self.get('fields')

    @fields.setter
    def fields(self, value):
        self['fields'] = self.get_fields(value)

    @property
    def label(self):
        """
        A short, human-readable label of this object.
        """
        return self.get('label')

    @label.setter
    def label(self, value):
        self['label'] = to_str(value)

    def to_input(self):
        return InputRecord(label=self.label, fields=self.fields)

    def to_output(self):
        return OutputRecord(label=self.label, fields=self.fields)

    @salad
    def get_fields(self, value):
        field_cls = self.get_field_cls()

        @salad
        def set_field(value):
            if isinstance(value, dict):
                return field_cls(**value)

        if value is not None:
            if is_instance_all(value, field_cls):
                return value
            elif is_instance_all(value, dict):
                return list(map(set_field, value))
            else:
                raise TypeError(
                    'Expected {}, got: {}'.format(field_cls, type(value))
                )
        else:
            return []

    def get_field_cls(self):
        raise NotImplementedError()


class InputRecord(RecordBase):
    def get_field_cls(self):
        return InputRecordField


class OutputRecord(RecordBase):
    def get_field_cls(self):
        return OutputRecordField


class RecordFieldBase(SchemaBase):
    def __init__(self, name, type, doc=None):
        super(RecordFieldBase, self).__init__()
        self.name = name
        self.type = type
        self.doc = doc

    @property
    def name(self):
        """
        The name of the field.
        """
        return self.get('name')

    @name.setter
    def name(self, value):
        self['name'] = to_str(value)

    @property
    def type(self):
        """
        The field type
        """
        return self.get('type')

    @type.setter
    def type(self, value):
        self['type'] = self.get_type(value)

    @property
    def doc(self):
        """
        A documentation string for this field
        """
        return self.get('doc')

    @doc.setter
    def doc(self, value):
        self['doc'] = to_str(value)

    def to_input(self):
        return InputRecordField(name=self.name, type=self.type, doc=self.doc)

    def to_output(self):
        return OutputRecordField(name=self.name, type=self.type, doc=self.doc)

    def get_type(self, value):
        raise NotImplementedError()


class InputRecordField(RecordFieldBase):

    def __init__(self, name, type, doc=None, input_binding=None, label=None):
        super(InputRecordField, self).__init__(
            name, type, doc=doc
        )
        self.input_binding = input_binding
        self.label = label

    @property
    def input_binding(self):
        return self.get('inputBinding')

    @input_binding.setter
    def input_binding(self, value):
        self['inputBinding'] = input_binding(value)

    def get_type(self, value):
        return input_schema_item(value)


class OutputRecordField(RecordFieldBase):

    def __init__(self, name, type, doc=None, output_binding=None):
        super(OutputRecordField, self).__init__(name, type, doc=doc)
        self.output_binding = output_binding

    @property
    def output_binding(self):
        return self.get('outputBinding')

    @output_binding.setter
    def output_binding(self, value):
        self['outputBinding'] = output_binding(value)

    def get_type(self, value):
        return output_schema_item(value)


class ArrayBase(SchemaBase):
    type = 'array'

    def __init__(self, items, label, type):
        super(ArrayBase, self).__init__()
        assert type == self.type
        self['type'] = self.type
        self.items_ = items
        self.label = label

    @property
    def items_(self):
        """
        Defines the type of the array elements.
        """
        return self.get('items')

    @items_.setter
    def items_(self, value):
        self['items'] = self.get_items(value)

    @property
    def label(self):
        """
        A short, human-readable label of this object.
        """
        return self.get('label')

    @label.setter
    def label(self, value):
        self['label'] = to_str(value)

    def to_input(self):
        return InputArray(items=self.items_, label=self.label)

    def to_output(self):
        return OutputArray(items=self.items_, label=self.label)

    def get_items(self, value):
        raise NotImplementedError()


class InputArray(ArrayBase):
    def __init__(self, items, label=None, input_binding=None, type='array'):
        super(InputArray, self).__init__(items, label, type)
        self.input_binding = input_binding

    @property
    def input_binding(self):
        return self.get('inputBinding')

    @input_binding.setter
    def input_binding(self, value):
        self['inputBinding'] = input_binding(value)

    def get_items(self, value):
        return input_schema_item(value)


class OutputArray(ArrayBase):
    def __init__(self, items, label=None, output_binding=None, type='array'):
        super(OutputArray, self).__init__(items, label, type)
        self.output_binding = output_binding

    @property
    def output_binding(self):
        return self.get('outputBinding')

    @output_binding.setter
    def output_binding(self, value):
        self['outputBinding'] = output_binding(value)

    def get_items(self, value):
        return output_schema_item(value)


class EnumBase(SchemaBase):
    type = 'enum'

    def __init__(self, symbols, label, type):
        super(EnumBase, self).__init__()
        assert type == self.type
        self['type'] = self.type
        self.symbols = symbols
        self.label = label

    @property
    def symbols(self):
        """
        Defines the set of valid symbols.
        """
        return self.get('symbols')

    @symbols.setter
    def symbols(self, value):
        self['symbols'] = to_slist(value)

    @property
    def label(self):
        """
        A short, human-readable label of this object.
        """
        return self.get('label')

    @label.setter
    def label(self, value):
        self['label'] = to_str(value)

    def to_input(self):
        return InputEnum(symbols=self.symbols, label=self.label)

    def to_output(self):
        return OutputEnum(symbols=self.symbols, label=self.label)


class InputEnum(EnumBase):
    def __init__(self, symbols, label=None, input_binding=None, type='enum'):
        super(InputEnum, self).__init__(
            symbols=symbols, label=label, type=type
        )
        self.input_binding = input_binding

    @property
    def input_binding(self):
        return self.get('inputBinding')

    @input_binding.setter
    def input_binding(self, value):
        self['inputBinding'] = input_binding(value)


class OutputEnum(EnumBase):
    def __init__(self, symbols, label=None, output_binding=None, type='enum'):
        super(OutputEnum, self).__init__(
            symbols=symbols, label=label, type=type
        )
        self.output_binding = output_binding

    @property
    def output_binding(self):
        return self.get('outputBinding')

    @output_binding.setter
    def output_binding(self, value):
        self['outputBinding'] = output_binding(value)


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
    elif isinstance(obj, (InputRecord, InputEnum, InputArray,
                          OutputRecord, OutputEnum, OutputArray)):  # schema
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
            return obj
    else:
        raise NotImplementedError(
            'Not implemented for type: {}'.format(type(obj))
        )
    return obj
