from sbg import cwl

with cwl.workflow('scatter_single.cwl', 'w') as wf:
    t1 = cwl.ExpressionTool('$({"out": inputs.word })', id='expr_tool1')
    t1.add_input(cwl.String(required=True), id='word', label='Word')
    t1.add_output(cwl.String(required=True), id='out', label='Word out')

    t2 = cwl.ExpressionTool(
        '$({"out": inputs.word.map(function(x){ return x.toLowerCase()}) })',
        id='expr_tool2'
    )
    t2.add_input(
        cwl.Array(cwl.String(), required=True), id='word', label='Word'
    )
    t2.add_output(
        cwl.Array(cwl.String(), required=True), id='out', label='Word out'
    )

    wf.add_step(t1, expose=['word'], scatter=['word'])
    wf.add_step(t2, expose=['out'])

    wf.add_connection('expr_tool1.out', 'expr_tool2.word')

    wf.add_requirement(cwl.InlineJavascript())
    wf.add_requirement(cwl.ScatterFeature())
