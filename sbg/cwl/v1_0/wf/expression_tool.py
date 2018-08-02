from sbg.cwl.v1_0.app import App
from sbg.cwl.v1_0.check import to_str
from sbg.cwl.v1_0.cmd.input import CommandInput
from sbg.cwl.v1_0.cmd.output import CommandOutput
from sbg.cwl.v1_0.wf.requirement import to_step_req


class ExpressionTool(App):
    """Execute an expression as a Workflow step."""
    class_ = 'ExpressionTool'

    def __init__(self, expression, cwl_version='v1.0',
                 inputs=None, outputs=None, id=None, requirements=None,
                 hints=None, label=None, doc=None, **kwargs):
        super(ExpressionTool, self).__init__(
            self.class_, cwl_version=cwl_version, inputs=inputs,
            outputs=outputs, id=id, requirements=requirements, hints=hints,
            label=label, doc=doc
        )
        self.expression = expression

    # region override
    def get_requirements(self, value):
        return to_step_req(value)

    def _get_cls(self):
        return ExpressionTool

    def _get_input_cls(self):
        return CommandInput

    def _get_output_cls(self):
        return CommandOutput

    # endregion

    # region properties
    @property
    def expression(self):
        """A long, human-readable description of this process object."""
        return self.get('expression')

    @expression.setter
    def expression(self, value):
        self['expression'] = to_str(value)

    # endregion
