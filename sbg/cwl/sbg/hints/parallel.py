from sbg.cwl.sbg.hints.hint import Hint
from sbg.cwl.v1_0.check import to_int


class MaxNumberOfParallelInstances(Hint):
    class_ = "sbg:maxNumberOfParallelInstances"

    def __init__(self, value):
        """
        Sets the maximum number of instances that can run in parallel for
        workflow execution.

        If a step is an inner workflow, its sbg:maxNumberOfParallelInstances
        will be overridden with the value from the outer workflow, even if it
        has not been set explicitly (i.e. the default value takes precedence).

        :param value: integer value
        """
        super(MaxNumberOfParallelInstances, self).__init__()
        self['class'] = self.class_
        self.value = value

    @property
    def value(self):
        """SBG SaveLogs value"""
        return self['value']

    @value.setter
    def value(self, value):
        self['value'] = to_int(value)
