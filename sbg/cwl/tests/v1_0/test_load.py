import pytest
import tempfile
from sbg import cwl


@pytest.mark.parametrize('app', [
    cwl.CommandLineTool(), cwl.Workflow(), cwl.ExpressionTool('${}')
])
def test_load_from_file(app):
    with tempfile.NamedTemporaryFile(delete=True) as f:
        app.dump(f.name)
        app_from_file = cwl.load(f.name)
        assert type(app_from_file) == type(app)


@pytest.mark.parametrize('app', [
    cwl.CommandLineTool(), cwl.Workflow(), cwl.ExpressionTool('${}')
])
def test_from_dict(app):
    app_type = type(app)
    raw_dict = app.to_dict()
    assert type(cwl.load(raw_dict)) == app_type
