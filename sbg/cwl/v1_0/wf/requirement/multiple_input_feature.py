from sbg.cwl.v1_0.base import Cwl


class MultipleInputFeature(Cwl):
    """
    Indicates that the wf platform must support multiple inbound data
    links listed in the source field of WorkflowStepInput.
    """
    class_ = 'MultipleInputFeatureRequirement'

    def __init__(self):
        super(MultipleInputFeature, self).__init__()
        self['class'] = self.class_
