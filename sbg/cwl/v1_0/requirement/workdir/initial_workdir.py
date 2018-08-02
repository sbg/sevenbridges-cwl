from sbg.cwl.v1_0.base import Cwl, salad
from sbg.cwl.v1_0.types import File, Directory
from sbg.cwl.v1_0.util import is_instance_all
from sbg.cwl.v1_0.requirement.workdir.dirent import Dirent


@salad
def to_listing(value):
    @salad
    def map_obj(obj):
        if isinstance(obj, str):
            return obj
        elif isinstance(obj, dict):
            if 'class' in obj:
                if obj['class'] == 'File':
                    return File(**obj)
                elif obj['class'] == 'Directory':
                    return Directory(**obj)
                else:
                    raise TypeError('Unsupported {}'.format(obj))
            elif 'entry' in obj:
                return Dirent(**obj)
            else:
                return obj
        else:
            raise TypeError('Unsupported {}'.format(obj))

    if value is not None:
        if isinstance(value, str) or is_instance_all(
                File, Directory, Dirent, str
        ):
            return value
        elif isinstance(value, list):
            return list(map(map_obj, value))
        else:
            raise TypeError('TypeError, got {}'.format(type(value)))


class InitialWorkDir(Cwl):
    """
    Define a list of files and subdirectories that must be created by the
    wf platform in the designated output directory prior to executing the
    command line tool.
    """
    class_ = 'InitialWorkDirRequirement'

    def __init__(self, listing):
        super(InitialWorkDir, self).__init__()
        self['class'] = self.class_
        self.listing = listing

    @property
    def listing(self):
        """
        The list of files or subdirectories that must be placed in the
        designated output directory prior to executing the command line tool.

        May be an expression. If so, the expression return value must validate
        as {type: array, items: [File, Directory]}.

        Files or Directories which are listed in the input parameters and
        appear in the InitialWorkDirRequirement listing must have their path
        set to their staged location in the designated output directory.
        If the same File or Directory appears more than once in the
        InitialWorkDirRequirement listing, the implementation must choose
        exactly one value for path; how this value is chosen is undefined.
        """
        return self.get('listing')

    @listing.setter
    def listing(self, value):
        self['listing'] = to_listing(value)
