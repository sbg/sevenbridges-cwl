from sbg.cwl.v1_0.base import Cwl


class StepInputExpression(Cwl):
    """
    Indicate that the wf platform must support the valueFrom field of
    WorkflowStepInput.
    """
    class_ = 'StepInputExpressionRequirement'

    def __init__(self):
        super(StepInputExpression, self).__init__()
        self['class'] = self.class_
