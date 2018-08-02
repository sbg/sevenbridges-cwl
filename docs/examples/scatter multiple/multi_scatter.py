from sbg import cwl

with cwl.workflow('multi_scatter.cwl', 'w') as wf:
    wf.id = 'multi_scatter'
    t1 = cwl.ExpressionTool(
        '$({"out": inputs.group1.concat(inputs.group2)})',
        id='expr_tool'
    )

    t1.add_input(cwl.String(required=True), 'group1')
    t1.add_input(cwl.String(required=True), 'group2')
    t1.add_output(cwl.String(required=True), 'out', label='Out')

    wf.add_step(
        t1,
        scatter=['group1', 'group2'],
        scatter_method=cwl.ScatterMethod.NESTED_CROSSPRODUCT
    )
    wf.add_requirement(cwl.InlineJavascript())
