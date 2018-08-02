from sbg.cwl.v1_0.base import Cwl
from sbg.cwl.v1_0.check import to_str_slist, to_bool, to_str
from sbg.cwl.v1_0.schema import output_binding, output_schema_item


class CommandOutput(Cwl):
    """
    An output parameter for a CommandLineTool.
    """

    def __init__(self, id=None, label=None, secondary_files=None,
                 streamable=None, doc=None, output_binding=None, format=None,
                 type=None):
        super(CommandOutput, self).__init__()
        self.id = id
        self.label = label
        self.secondary_files = secondary_files
        self.streamable = streamable
        self.doc = doc
        self.output_binding = output_binding
        self.format = format
        self.type = type

    @property
    def id(self):
        """
        The unique identifier for this parameter object.
        """
        return self.get('id')

    @id.setter
    def id(self, value):
        self['id'] = to_str(value)

    @property
    def label(self):
        """
        A short, human-readable label of this object.
        """
        return self.get('label')

    @label.setter
    def label(self, value):
        self['label'] = to_str(value)

    @property
    def secondary_files(self):
        """
        Only valid when type File or is an array of items File.

        Provides a pattern or expression specifying files or directories that
        must be included alongside the primary file. All listed secondary files
        must be present. An implementation may fail wf execution if an
        expected secondary file does not exist.

        If the value is an expression, the value of self in the expression must
        be the primary input or output File object to which this binding
        applies .The basename, nameroot and nameext fields must be present in
        self. For CommandLineTool outputs the path field must also be present.
        The expression must return a filename string relative to the path to
        the primary File, a File or Directory object with either path or
        location and basename fields set, or an array consisting of strings or
        File or Directory objects. It is legal to reference an unchanged File
        or Directory object taken from input as a secondaryFile.

        To work on non-filename-preserving storage systems, portable tool
        descriptions should avoid constructing new values from location, but
        should construct relative references using basename or nameroot
        instead.

        If a value in secondaryFiles is a string that is not an expression,
        it specifies that the following pattern should be applied to the path
        of the primary file to yield a filename relative to the primary File

        1. If string begins with one or more caret ^ characters, for each
        caret, remove the last file extension from the path (the last period .
        and all following characters). If there are no file extensions,
        the path is unchanged.
        2. Append the remainder of the string to the end of the file path.
        """
        return self.get('secondaryFiles')

    @secondary_files.setter
    def secondary_files(self, value):
        self['secondaryFiles'] = to_str_slist(value)

    @property
    def streamable(self):
        """
        Only valid when type File or is an array of items File.

        A value of true indicates that the file is read or written sequentially
        without seeking. An implementation may use this flag to indicate
        whether it is valid to stream file contents using a named pipe.
        Default false.
        """
        return self.get('streamable')

    @streamable.setter
    def streamable(self, value):
        self['streamable'] = to_bool(value)

    @property
    def doc(self):
        """
        A documentation string for this type, or an array of strings which
        should be concatenated.
        """
        return self.get('doc')

    @doc.setter
    def doc(self, value):
        self['doc'] = to_str_slist(value)

    @property
    def output_binding(self):
        """
        Describes how to handle the outputs of a process.
        """
        return self.get('outputBinding')

    @output_binding.setter
    def output_binding(self, value):
        self['outputBinding'] = output_binding(value)

    @property
    def format(self):
        """
        Only valid when type File or is an array of items File.

        This is the file format that will be assigned to the output parameter.
        """
        return self.get('format')

    @format.setter
    def format(self, value):
        self['format'] = to_str(value)

    @property
    def type(self):
        """
        Specify valid types of data that may be assigned to this parameter.
        """
        return self.get('type')

    @type.setter
    def type(self, value):
        self['type'] = output_schema_item(value)
