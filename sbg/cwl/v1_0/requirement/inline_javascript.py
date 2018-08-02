from sbg.cwl.v1_0.base import Cwl
from sbg.cwl.v1_0.check import to_slist


class InlineJavascript(Cwl):
    """
    Indicates that the wf platform must support inline Javascript
    expressions. If this requirement is not present, the wf platform must
    not perform expression interpolatation.
    """
    class_ = 'InlineJavascriptRequirement'

    def __init__(self, expression_lib=None):
        super(InlineJavascript, self).__init__()
        self['class'] = self.class_
        self.expression_lib = expression_lib

    @property
    def expression_lib(self):
        """
        Additional code fragments that will also be inserted before executing
        the expression code. Allows for function definitions that may be called
        from CWL expressions.
        """
        return self.get('expressionLib')

    @expression_lib.setter
    def expression_lib(self, value):
        self['expressionLib'] = to_slist(value)
