from sbg.cwl.v1_0.util import from_file
from sbg.cwl.v1_0.wf.workflow import Workflow
from sbg.cwl.v1_0.cmd.tool import CommandLineTool
from sbg.cwl.v1_0.wf.expression_tool import ExpressionTool


def load(cwl):
    """
    Loads CWL document from file or JSON object and instantiate object of a
    class specified by key ``class`` inside a document.

    :param cwl: file (can be either in ``JSON`` or ``YAML`` format)
    :return: depending on ``class`` can be either an instance of
             ``CommandLineTool`` or ``ExpressionTool`` or ``Workflow``
    """

    if not isinstance(cwl, dict):
        cwl = from_file(cwl)
    if isinstance(cwl, dict):
        if "class" in cwl:
            if cwl['class'] == 'CommandLineTool':
                return CommandLineTool(**cwl)
            elif cwl['class'] == 'Workflow':
                return Workflow(**cwl)
            elif cwl['class'] == 'ExpressionTool':
                return ExpressionTool(**cwl)
            else:
                raise ValueError("Unsupported class: {}".format(cwl['class']))
        else:
            raise ValueError("Missing class key.")
    else:
        raise ValueError('Type Error, got: {}'.format(type(cwl)))
