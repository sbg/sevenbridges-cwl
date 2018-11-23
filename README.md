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

### Official releases
Official releases are available via `pip install sevenbridges-cwl` (This is the [pypi entry](https://pypi.org/project/sevenbridges-cwl/) for this project)

### Development versions
To obtain unreleased versions: 

- `git clone` this repository 
- `cd sevenbridges-cwl && pip install .`

The `master` branch is for more stable code while `develop` is for cutting edge features being currently worked on

## <a name="docs">Docs</a>

Complete documentation can be found [here](https://sevenbridges-cwl.readthedocs.io/en/latest/quickstart.html).

If you are interested in reviewing this documentation locally, clone this 
repository, position yourself in the `docs` directory and after installing 
`requirements-dev.txt`, invoke:

```
make html
```

## <a name="tests">Run Tests</a>

In order to run tests clone this repository, position yourself in the root of 
the cloned project and, after installing `requirements-dev.txt`, invoke: 
```
pytest
```

## <a name="examples">Examples</a>

The following code will give a brief overview of what this package can offer through 
simple examples. 

**A Complete list of all examples can be found <a href="https://github.com/sbg/sevenbridges-cwl/tree/master/docs/examples">here</a>.**

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
