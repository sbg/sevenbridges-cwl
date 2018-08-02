from sbg.cwl.v1_0.base import Cwl, salad
from sbg.cwl.v1_0.util import is_instance_all
from sbg.cwl.v1_0.schema import InputEnum, InputRecord, InputArray


@salad
def to_schemadef_type(value):
    @salad
    def map_obj(obj):
        if isinstance(obj, dict):
            if obj['type'] == 'enum':
                return InputEnum(**obj)
            elif obj['type'] == 'record':
                return InputRecord(**obj)
            elif obj['type'] == 'array':
                return InputArray(**obj)
            else:
                raise ValueError(
                    "Unsupported type for shemadef: {}".format(obj['type'])
                )
        return obj

    if value is not None:
        if is_instance_all(value, InputRecord, InputEnum, InputArray):
            return value
        elif isinstance(value, list):
            return list(map(map_obj, value))
        else:
            raise TypeError(
                'Expected list[SchemaDef requirements], got {}'.format(
                    type(value))
            )


class SchemaDef(Cwl):
    """
    This field consists of an array of type definitions which must be used when
    interpreting the inputs and outputs fields. When a type field contain a
    IRI, the implementation must check if the type is defined in schemaDefs
    and use that definition. If the type is not found in schemaDefs,
    it is an error. The entries in schemaDefs must be processed in the order
    listed such that later schema definitions may refer to earlier schema
    definitions.
    """
    class_ = 'SchemaDefRequirement'

    def __init__(self, types):
        super(SchemaDef, self).__init__()
        self['class'] = self.class_
        self.types = types

    @property
    def types(self):
        """
        The list of type definitions.
        """
        return self.get('types')

    @types.setter
    def types(self, value):
        self['types'] = to_schemadef_type(value)
