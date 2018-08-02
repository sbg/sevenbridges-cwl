from sbg.cwl.v1_0.base import Cwl, salad
from sbg.cwl.v1_0.requirement.software.software_package import (
    SoftwarePackage
)


@salad
def create_soft_packages(value):
    @salad
    def map_to_cls(obj):
        return SoftwarePackage(**obj)

    if value is not None:
        if isinstance(value, list):
            return list(map(map_to_cls, value))
        elif isinstance(value, dict):
            packages = []
            for k, v in value.items():
                if isinstance(v, dict):
                    v = map_to_cls(v)
                else:
                    v = SoftwarePackage(k, specs=v)
                packages.append(v)
            return packages
        else:
            raise TypeError('Unsupported type: {}'.format(type(value)))


class Software(Cwl):
    """
    A list of software packages that should be configured in the environment of
    the defined process.
    """
    class_ = 'SchemaDefRequirement'

    def __init__(self, packages):
        super(Software, self).__init__()
        self['class'] = self.class_
        self.packages = packages

    @property
    def packages(self):
        """
        The (optional) versions of the software that are known to be
        compatible.
        """
        return self.get('packages')

    @packages.setter
    def packages(self, value):
        self['packages'] = create_soft_packages(value)
