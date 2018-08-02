from sbg.cwl.v1_0.base import Cwl
from sbg.cwl.v1_0.check import to_str


class EnvironmentDef(Cwl):
    """
    Define an environment variable that will be set in the runtime environment
    by the wf platform when executing the command line tool. May be the
    result of executing an expression, such as getting a parameter from input.
    """

    def __init__(self, env_name, env_value):
        super(EnvironmentDef, self).__init__()
        self.env_name = env_name
        self.env_value = env_value

    @property
    def env_name(self):
        """
        The environment variable name
        """
        return self.get('envName')

    @env_name.setter
    def env_name(self, value):
        self['envName'] = to_str(value)

    @property
    def env_value(self):
        """
        The environment variable name
        """
        return self.get('envValue')

    @env_value.setter
    def env_value(self, value):
        self['envValue'] = to_str(value)
