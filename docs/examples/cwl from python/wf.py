from sbg import cwl


# First node
@cwl.to_tool(
    inputs=dict(x=cwl.String()),
    outputs=dict(out=cwl.Float(required=True)),
    docker='images.sbgenomics.com/filip_tubic/ubuntu1604py'
)
def to_float(x):
    return dict(out=float(x))


# Second node
@cwl.to_tool(
    inputs=dict(x=cwl.Float(), n=cwl.Int()),
    outputs=dict(out=cwl.Float()),
    docker='images.sbgenomics.com/filip_tubic/ubuntu1604py'
)
def times_n(x, n=10):
    return dict(out=x * n)


with cwl.workflow('wf.cwl', 'w') as wf:
    # create tools
    t1 = to_float()
    t2 = times_n()

    # steps
    wf.add_step(t1, expose=['x'])
    wf.add_step(t2, expose=['n', 'out'])

    # add connections
    wf.add_connection('{}.out'.format(t1.id), '{}.x'.format(t2.id))
