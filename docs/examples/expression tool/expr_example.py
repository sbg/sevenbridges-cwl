from sbg import cwl

with cwl.workflow('expr_example.cwl', 'w') as wf:
    t = cwl.ExpressionTool('$({"out": inputs.word })', id='expr_tool')

    t.add_input(cwl.String(required=True), id='word', label='Word')
    t.add_output(cwl.String(required=True), id='out', label='Word out')

    wf.add_step(t)
    wf.add_requirement(cwl.InlineJavascript())
