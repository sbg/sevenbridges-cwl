from sbg.cwl.v1_0.base import Cwl


class ScatterFeature(Cwl):
    """
    Indicates that the wf platform must support the scatter and
    scatterMethod fields of WorkflowStep.
    """
    class_ = 'ScatterFeatureRequirement'

    def __init__(self):
        super(ScatterFeature, self).__init__()
        self['class'] = self.class_
