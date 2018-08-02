from sbg.cwl.v1_0.base import Cwl, salad
from sbg.cwl.v1_0.check import to_str, to_int
from sbg.cwl.v1_0.util import is_instance_all


@salad
def to_file_dir_list(value):
    @salad
    def map_dict(d):
        if d['class'] == 'Directory':
            return Directory(**d)
        elif d['class'] == 'File':
            return File(**d)
        else:
            raise ValueError('Unsupported class')

    if value is not None:
        if is_instance_all(value, File, Directory):
            return value
        elif is_instance_all(value, dict):
            return list(map(map_dict, value))
        else:
            raise TypeError(
                'Expected list[File|Directory], got: {}'.format(
                    type(value))
            )


class Primitive(object):
    # no value
    NULL = 'null'
    # a binary value
    BOOLEAN = 'boolean'
    # 32-bit signed integer
    INT = 'int'
    # 64-bit signed integer
    LONG = 'long'
    # single precision (32-bit) IEEE 754 floating-point number
    FLOAT = 'float'
    # double precision (64-bit) IEEE 754 floating-point number
    DOUBLE = 'double'
    # Unicode character sequence
    STRING = 'string'
    # A File object
    FILE = 'File'
    # A Directory object
    DIRECTORY = 'Directory'
    ANY = 'Any'


def is_primitive(t):
    """
    Checks by CWL v1.0 specification if object ``t`` is primitive type.
    """

    primitives = [
        Primitive.BOOLEAN, Primitive.INT, Primitive.LONG,
        Primitive.FLOAT,
        Primitive.DOUBLE, Primitive.STRING, Primitive.FILE,
        Primitive.DIRECTORY, Primitive.NULL, Primitive.ANY
    ]
    non_req = []
    for p in primitives:
        non_req += ["{}?".format(p), [Primitive.NULL, p]]

    return t in primitives + non_req


def is_number(t):
    """
    Checks by CWL v1.0 specification if object ``t`` is number type.
    """
    return t in (
        Primitive.INT, Primitive.LONG, Primitive.FLOAT, Primitive.DOUBLE
    )


class File(Cwl):
    """
    Represents a file (or group of files when secondaryFiles is provided) that
    will be accessible by tools using standard POSIX file system call API such
    as open(2) and read(2).

    Files are represented as objects with class of File. File objects have a
    number of properties that provide metadata about the file.

    The location property of a File is a URI that uniquely identifies the file.
    Implementations must support the file:// URI scheme and may support other
    schemes such as http://. The value of location may also be a relative
    reference, in which case it must be resolved relative to the URI of the
    document it appears in. Alternately to location, implementations must also
    accept the path property on File, which must be a filesystem path available
    on the same host as the CWL runner (for inputs) or the runtime environment
    of a command line tool execution (for command line tool outputs).

    If no location or path is specified, a file object must specify contents
    with the UTF-8 text content of the file. This is a "file literal". File
    literals do not correspond to external resources, but are created on disk
    with contents with when needed for a executing a tool. Where appropriate,
    expressions can return file literals to define new files on a runtime.
    The maximum size of contents is 64 kilobytes.

    The basename property defines the filename on disk where the file is
    staged.
    This may differ from the resource name. If not provided, basename must be
    computed from the last path part of location and made available to
    expressions.

    The secondaryFiles property is a list of File or Directory objects that
    must be staged in the same directory as the primary file. It is an error
    for file names to be duplicated in secondaryFiles.

    The size property is the size in bytes of the File. It must be computed
    from the resource and made available to expressions. The checksum field
    contains a cryptographic hash of the file content for use it verifying
    file contents.
    Implementations may, at user option, enable or disable computation of the
    checksum field for performance or other reasons. However, the ability to
    compute output checksums is required to pass the CWL conformance test
    suite.

    When executing a CommandLineTool, the files and secondary files may be
    staged to an arbitrary directory, but must use the value of basename for
    the filename. The path property must be file path in the context of the
    tool execution runtime (local to the compute node, or within the executing
    container). All computed properties should be available to expressions.
    File literals also must be staged and path must be set.

    When collecting CommandLineTool outputs, glob matching returns file paths
    (with the path property) and the derived properties. This can all be
    modified by outputEval. Alternately, if the file cwl.outputs.json is
    present in the output, outputBinding is ignored.

    File objects in the output must provide either a location URI or a path
    property in the context of the tool execution runtime (local to the compute
    node, or within the executing container).

    When evaluating an ExpressionTool, file objects must be referenced via
    location (the expression tool does not have access to files on disk so
    path is meaningless) or as file literals. It is legal to return a file
    object with an existing location but a different basename. The loadContents
    field of ExpressionTool inputs behaves the same as on CommandLineTool
    inputs, however it is not meaningful on the outputs.

    An ExpressionTool may forward file references from input to output by using
    the same value for location.
    """
    class_ = 'File'

    def __init__(self, location=None, path=None, basename=None,
                 dirname=None, nameroot=None, nameext=None, checksum=None,
                 size=None, secondary_files=None, format=None, contents=None):
        super(File, self).__init__()
        self['class'] = self.class_
        self.location = location
        self.path = path
        self.basename = basename
        self.dirname = dirname
        self.nameroot = nameroot
        self.nameext = nameext
        self.checksum = checksum
        self.size = size
        self.secondary_files = secondary_files
        self.format = format
        self.contents = contents

    def add_secondary_file(self, file):
        if not self.secondary_files:
            self.secondary_files = []
        self.secondary_files.append(file)

    @property
    def location(self):
        """
        An IRI that identifies the file resource. This may be a relative
        reference, in which case it must be resolved using the base IRI of the
        document. The location may refer to a local or remote resource;
        the implementation must use the IRI to retrieve file content.
        If an implementation is unable to retrieve the file content stored at
        a remote resource (due to unsupported protocol, access denied,
        or other issue) it must signal an error.

        If the location field is not provided, the contents field must be
        provided. The implementation must assign a unique identifier for
        the location field.

        If the path field is provided but the location field is not,
        an implementation may assign the value of the path field to location,
        then follow the rules above.
        """
        return self.get('location')

    @location.setter
    def location(self, value):
        self['location'] = to_str(value)

    @property
    def path(self):
        """
        The local host path where the File is available when a CommandLineTool
        is executed. This field must be set by the implementation. The final
        path component must match the value of basename. This field must not be
        used in any other context. The command line tool being executed must be
        able to to access the file at path using the POSIX open(2) syscall.

        As a special case, if the path field is provided but the location field
        is not, an implementation may assign the value of the path field to
        location, and remove the path field.
        """
        return self.get('path')

    @path.setter
    def path(self, value):
        self['path'] = to_str(value)

    @property
    def basename(self):
        """
        The base name of the file, that is, the name of the file without any
        leading directory path. The base name must not contain a slash /.

        If not provided, the implementation must set this field based on the
        location field by taking the final path component after parsing
        location as an IRI. If basename is provided, it is not required to
        match the value from location.

        When this file is made available to a CommandLineTool, it must be named
        with basename, i.e. the final component of the path field must match
        basename.
        """
        return self.get('basename')

    @basename.setter
    def basename(self, value):
        self['basename'] = to_str(value)

    @property
    def dirname(self):
        """
        The name of the directory containing file, that is, the path leading up
        to the final slash in the path such that
        dirname + '/' + basename == path.

        The implementation must set this field based on the value of path
        prior to evaluating parameter references or expressions in
        a CommandLineTool document. This field must not be used in any other
        context.
        """
        return self.get('dirname')

    @dirname.setter
    def dirname(self, value):
        self['dirname'] = to_str(value)

    @property
    def nameroot(self):
        """
        The basename root such that nameroot + nameext == basename, and nameext
        is empty or begins with a period and contains at most one period.
        For the purposess of path splitting leading periods on the basename
        are ignored; a basename of .cshrc will have a nameroot of .cshrc.

        The implementation must set this field automatically based on the value
        of basename prior to evaluating parameter references or expressions.
        """
        return self.get('nameroot')

    @nameroot.setter
    def nameroot(self, value):
        self['nameroot'] = to_str(value)

    @property
    def nameext(self):
        """
        The basename extension such that nameroot + nameext == basename, and
        nameext is empty or begins with a period and contains at most one
        period. Leading periods on the basename are ignored; a basename of
        .cshrc will have an empty nameext.

        The implementation must set this field automatically based on the
        value of basename prior to evaluating parameter references
        or expressions.
        """
        return self.get('nameext')

    @nameext.setter
    def nameext(self, value):
        self['nameext'] = to_str(value)

    @property
    def checksum(self):
        """
        Optional hash code for validating file integrity.
        Currently must be in the form "sha1$ + hexadecimal string" using
        the SHA-1 algorithm.
        """
        return self.get('checksum')

    @checksum.setter
    def checksum(self, value):
        self['checksum'] = to_str(value)

    @property
    def size(self):
        """
        Optional file size.
        """
        return self.get('size')

    @size.setter
    def size(self, value):
        self['size'] = to_int(value)

    @property
    def secondary_files(self):
        """
        A list of additional files or directories that are associated with the
        primary file and must be transferred alongside the primary file.
        Examples include indexes of the primary file, or external references
        which must be included when loading primary document.
        A file object listed in secondaryFiles may itself include
        secondaryFiles for which the same rules apply.
        """
        return self.get('secondaryFiles')

    @secondary_files.setter
    def secondary_files(self, value):
        self['secondaryFiles'] = to_file_dir_list(value)

    @property
    def format(self):
        """
        The format of the file: this must be an IRI of a concept node that
        represents the file format, preferrably defined within an ontology.
        If no ontology is available, file formats may be tested by exact match.

        Reasoning about format compatability must be done by checking that
        an input file format is the same, owl:equivalentClass or
        rdfs:subClassOf the format required by the input parameter.
        owl:equivalentClass is transitive with rdfs:subClassOf, e.g.
        if <B> owl:equivalentClass <C> and <B> owl:subclassOf <A> then infer
        <C> owl:subclassOf <A>.

        File format ontologies may be provided in the "$schema" metadata
        at the root of the document. If no ontologies are specified in $schema,
        the runtime may perform exact file format matches.
        """
        return self.get('format')

    @format.setter
    def format(self, value):
        self['format'] = to_str(value)

    @property
    def contents(self):
        """
        File contents literal. Maximum of 64 KiB.

        If neither location nor path is provided, contents must be non-null.
        The implementation must assign a unique identifier for
        the location field. When the file is staged as input to
        CommandLineTool, the value of contents must be written to a file.

        If loadContents of inputBinding or outputBinding is true and location
        is valid, the implementation must read up to the first 64 KiB of text
        from the file and place it in the "contents" field.
        """
        return self.get('contents')

    @contents.setter
    def contents(self, value):
        self['contents'] = to_str(value)


class Directory(Cwl):
    """
    Represents a directory to present to a command line tool.

    Directories are represented as objects with class of Directory.
    Directory objects have a number of properties that provide
    metadata about the directory.

    The location property of a Directory is a URI that uniquely identifies
    the directory. Implementations must support the file:// URI scheme and may
    support other schemes such as http://. Alternately to location,
    implementations must also accept the path property on Direcotry,
    which must be a filesystem path available on the same host as the CWL
    runner (for inputs) or the runtime environment of a command line tool
    execution (for command line tool outputs).

    A Directory object may have a listing field. This is a list of File and
    Directory objects that are contained in the Directory. For each entry
    in listing, the basename property defines the name of the File
    or Subdirectory when staged to disk. If listing is not provided, the
    implementation must have some way of fetching the Directory listing at
    runtime based on the location field.

    If a Directory does not have location, it is a Directory literal.
    A Directory literal must provide listing. Directory literals must be
    created on disk at runtime as needed.

    The resources in a Directory literal do not need to have any implied
    relationship in their location. For example, a Directory listing may
    contain two files located on different hosts. It is the responsibility of
    the runtime to ensure that those files are staged to disk appropriately.
    Secondary files associated with files in listing must also be staged
    to the same Directory.

    When executing a CommandLineTool, Directories must be recursively staged
    first and have local values of path assigend.

    Directory objects in CommandLineTool output must provide either
    a location URI or a path property in the context of the tool execution
    runtime (local to the compute node, or within the executing container).

    An ExpressionTool may forward file references from input to output by using
    the same value for location.

    Name conflicts (the same basename appearing multiple times in listing
    or in any entry in secondaryFiles in the listing) is a fatal error.
    """
    class_ = 'Directory'

    def __init__(self, location=None, path=None, basename=None, listing=None):
        super(Directory, self).__init__()
        self['class'] = self.class_
        self.location = location
        self.path = path
        self.basename = basename
        self.listing = listing

    def add_listing(self, i):
        if not self.listing:
            self.listing = []
        self.listing.append(i)

    @property
    def location(self):
        """
        An IRI that identifies the directory resource. This may be a relative
        reference, in which case it must be resolved using the base IRI of
        the document. The location may refer to a local or remote resource.
        If the listing field is not set, the implementation must use
        the location IRI to retrieve directory listing. If an implementation is
        unable to retrieve the directory listing stored at a remote resource
        (due to unsupported protocol, access denied, or other issue)
        it must signal an error.

        If the location field is not provided, the listing field must
        be provided. The implementation must assign a unique identifier
        for the location field.

        If the path field is provided but the location field is not,
        an implementation may assign the value of the path field to location,
        then follow the rules above.
        """
        return self.get('location')

    @location.setter
    def location(self, value):
        self['location'] = to_str(value)

    @property
    def path(self):
        """
        The local path where the Directory is made available prior to executing
        a CommandLineTool. This must be set by the implementation.
        This field must not be used in any other context. The command line tool
        being executed must be able to to access the directory at path using
        the POSIX opendir(2) syscall.
        """
        return self.get('path')

    @path.setter
    def path(self, value):
        self['path'] = to_str(value)

    @property
    def basename(self):
        """
        The base name of the directory, that is, the name of the file without
        any leading directory path. The base name must not contain a slash /.

        If not provided, the implementation must set this field based on the
        location field by taking the final path component after parsing
        location as an IRI. If basename is provided, it is not required to
        match the value from location.

        When this file is made available to a CommandLineTool, it must be named
        with basename, i.e. the final component of the path field must match
        basename.
        """
        return self.get('basename')

    @basename.setter
    def basename(self, value):
        self['basename'] = to_str(value)

    @property
    def listing(self):
        """
        List of files or subdirectories contained in this directory.
        The name of each file or subdirectory is determined by the basename
        field of each File or Directory object. It is an error if a File shares
        a basename with any other entry in listing. If two or more Directory
        object share the same basename, this must be treated as equivalent to a
        single subdirectory with the listings recursively merged.
        """
        return self.get('listing')

    @listing.setter
    def listing(self, value):
        self['listing'] = to_file_dir_list(value)
