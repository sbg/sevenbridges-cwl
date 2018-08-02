from sbg.cwl.v1_0.base import Cwl


class SubworkflowFeature(Cwl):
    """
    Indicates that the wf platform must support nested workflows in the
    run field of WorkflowStep.
    """
    class_ = 'SubworkflowFeatureRequirement'

    def __init__(self):
        super(SubworkflowFeature, self).__init__()
        self['class'] = self.class_
