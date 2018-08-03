SevenBridges CWL 
===========================

# Table of contents
1. [Overview](#overview)
2. [Install](#install)
3. [Docs](#docs)
4. [Run tests](#tests)
5. [Examples](#examples)
    - [Run workflow on a SevenBridges platform](#example1)

## <a name="overview">Overview</a>

**SevenBridges CWL** package provides python bindings for 
_Common Workflow Language_. It is intended for developers who want to use 
python code to generate CWL documents. If creating a document through the GUI
is preferable, then look at the 
[Rabix Composer](https://github.com/rabix/composer).

## <a name="install">Install</a>

1. Clone
2. Redirect to **sevenbridges-cwl** and install: 
`cd sevenbridges-cwl && pip install .`

## <a name="docs">Docs</a>

If you are interested in reviewing this documentation locally, clone this 
repository, position yourself in the docs directory and after installing 
requirements-dev.txt, invoke:

```
make html
```

## <a name="tests">Run Tests</a>

In order to run tests clone this repository, position yourself in the root of 
the cloned project and, after installing requirements-dev.txt, invoke: 
```
pytest
```

## <a name="examples">Examples</a>

The following will give a brief overview of what this package can offer through 
simple examples. Complete list of all examples can be found 
<a href="docs/examples/">here</a>.

### <a name="example1">Run workflow on a SevenBridges platform</a>

```python
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


wf = cwl.Workflow()

# create tools
t1 = to_float()
t2 = times_n()

# steps
wf.add_step(t1, expose=['x'])
wf.add_step(t2, expose=['n', 'out'])

# add connections
wf.add_connection(f'{t1.id}.out', f'{t2.id}.x')

# Session on a SBG platform
session = cwl.Session(profile='<your_profile>')

session.run('<your_project>', wf, inputs={'x': '10.2'})
``` 
