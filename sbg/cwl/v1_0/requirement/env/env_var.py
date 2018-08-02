from sbg.cwl.v1_0.base import Cwl, salad
from sbg.cwl.v1_0.requirement.env.env_def import EnvironmentDef


@salad
def create_envdef(value):
    @salad
    def map_to_cls(obj):
        return EnvironmentDef(**obj)

    if value is not None:
        if isinstance(value, list):
            return list(map(map_to_cls, value))
        elif isinstance(value, dict):
            defs = []
            for k, v in value.items():
                if isinstance(v, dict):
                    v = map_to_cls(v)
                else:
                    v = EnvironmentDef(k, v)
                defs.append(v)
            return defs
        else:
            raise TypeError('Unsupported type: {}'.format(type(value)))


class EnvVar(Cwl):
    """
    Define a list of environment variables which will be set in the execution
    environment of the tool. See EnvironmentDef for details.
    """
    class_ = 'EnvVarRequirement'

    def __init__(self, env_def):
        super(EnvVar, self).__init__()
        self['class'] = self.class_
        self.env_def = env_def

    @property
    def env_def(self):
        """
        The list of environment variables.
        """
        return self.get('envDef')

    @env_def.setter
    def env_def(self, value):
        self['envDef'] = create_envdef(value)
