from sbg.cwl.v1_0.cmd.output import CommandOutput
from sbg.cwl.v1_0.check import to_str, to_str_slist


class WorkflowOutput(CommandOutput):

    def __init__(self, id=None, label=None, secondary_files=None,
                 streamable=None, doc=None, output_binding=None, format=None,
                 type=None, output_source=None, link_merge=None):
        super(WorkflowOutput, self).__init__(
            id=id,
            label=label,
            secondary_files=secondary_files,
            streamable=streamable,
            doc=doc,
            output_binding=output_binding,
            format=format,
            type=type
        )
        self.output_source = output_source
        self.link_merge = link_merge

    # region properties

    @property
    def output_source(self):
        """
        Specifies one or more wf parameters that supply the value of to
        the output parameter.
        """
        return self.get('outputSource')

    @output_source.setter
    def output_source(self, value):
        self['outputSource'] = to_str_slist(value)

    @property
    def link_merge(self):
        """
        The method to use to merge multiple sources into a single array.
        If not specified, the default method is "merge_nested".
        """
        return self.get('linkMerge')

    @link_merge.setter
    def link_merge(self, value):
        self['linkMerge'] = to_str(value)
    # endregion
