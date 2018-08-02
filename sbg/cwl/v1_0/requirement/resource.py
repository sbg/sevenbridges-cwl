from sbg.cwl.v1_0.base import Cwl
from sbg.cwl.v1_0.check import to_str_int


class Resource(Cwl):
    """
    Specify basic hardware resource requirements.

    "min" is the minimum amount of a resource that must be reserved to schedule
    a job. If "min" cannot be satisfied, the job should not be run.

    "max" is the maximum amount of a resource that the job shall be permitted
    to use. If a node has sufficient resources, multiple jobs may be scheduled
    on a single node provided each job's "max" resource requirements are met.
    If a job attempts to exceed its "max" resource allocation, an
    implementation may deny additional resources, which may result in job
    failure.

    If "min" is specified but "max" is not, then "max" == "min" If "max" is
    specified by "min" is not, then "min" == "max".

    It is an error if max < min.

    It is an error if the value of any of these fields is negative.

    If neither "min" nor "max" is specified for a resource, an implementation
    may provide a default.
    """
    class_ = 'ResourceRequirement'

    def __init__(self, cores_min=None,
                 cores_max=None, ram_min=None, ram_max=None, tmpdir_min=None,
                 tmpdir_max=None, outdir_min=None, outdir_max=None):
        super(Resource, self).__init__()
        self['class'] = self.class_
        self.cores_min = cores_min
        self.cores_max = cores_max
        self.ram_min = ram_min
        self.ram_max = ram_max
        self.tmpdir_min = tmpdir_min
        self.tmpdir_max = tmpdir_max
        self.outdir_min = outdir_min
        self.outdir_max = outdir_max

    @property
    def cores_min(self):
        """
        Minimum reserved number of CPU cores
        """
        return self.get('coresMin')

    @cores_min.setter
    def cores_min(self, value):
        self['coresMin'] = to_str_int(value)

    @property
    def cores_max(self):
        """
        Maximum reserved number of CPU cores
        """
        return self.get('coresMax')

    @cores_max.setter
    def cores_max(self, value):
        self['coresMax'] = to_str_int(value)

    @property
    def ram_min(self):
        """
        Minimum reserved RAM in mebibytes (2**20)
        """
        return self.get('ramMin')

    @ram_min.setter
    def ram_min(self, value):
        self['ramMin'] = to_str_int(value)

    @property
    def ram_max(self):
        """
        Maximum reserved RAM in mebibytes (2**20)
        """
        return self.get('ramMax')

    @ram_max.setter
    def ram_max(self, value):
        self['ramMax'] = to_str_int(value)

    @property
    def tmpdir_min(self):
        """
        Minimum reserved filesystem based storage for the designated temporary
        directory, in mebibytes (2**20)
        """
        return self.get('tmpdirMin')

    @tmpdir_min.setter
    def tmpdir_min(self, value):
        self['tmpdirMin'] = to_str_int(value)

    @property
    def tmpdir_max(self):
        """
        Maximum reserved filesystem based storage for the designated temporary
        directory, in mebibytes (2**20)
        """
        return self.get('tmpdirMax')

    @tmpdir_max.setter
    def tmpdir_max(self, value):
        self['tmpdirMax'] = to_str_int(value)

    @property
    def outdir_min(self):
        """
        Minimum reserved filesystem based storage for the designated output
        directory, in mebibytes (2**20)
        """
        return self.get('outdirMin')

    @outdir_min.setter
    def outdir_min(self, value):
        self['outdirMin'] = to_str_int(value)

    @property
    def outdir_max(self):
        """
        Maximum reserved filesystem based storage for the designated output
        directory, in mebibytes (2**20)
        """
        return self.get('outdirMax')

    @outdir_max.setter
    def outdir_max(self, value):
        self['outdirMax'] = to_str_int(value)
