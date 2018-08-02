import pytest
from sbg import cwl
import unittest.mock as mock
from sbg.cwl.sbg.session import Session, Project, Api
from sevenbridges.http.error_handlers import (
    general_error_sleeper, maintenance_sleeper, rate_limit_sleeper
)


@pytest.fixture(scope='function')
def tool():
    return cwl.CommandLineTool(id='foo')


@pytest.mark.parametrize('kwargs', [
    {'token': 't', 'endpoint': 'e'},
    {'token': 't', 'endpoint': 'e', 'profile': 'p'}
])
def test_init_api_token_endpoint(kwargs):
    with mock.patch('sbg.cwl.sbg.session.Api') as api_mock:
        Session.init_api(**kwargs)

        called_with = {
            'error_handlers': [
                rate_limit_sleeper,
                maintenance_sleeper,
                general_error_sleeper
            ],
            'token': kwargs.get('token'),
            'url': kwargs.get('endpoint')
        }

        api_mock.assert_called_with(**called_with)


@pytest.mark.parametrize('kwargs', [{}, {'profile': 'p'}])
def test_init_api_profile(kwargs):
    with mock.patch('sbg.cwl.sbg.session.Api') as api_mock:
        with mock.patch('sbg.cwl.sbg.session.Config') as conf_mock:
            Session.init_api(**kwargs)
            called_with = {
                'error_handlers': [
                    rate_limit_sleeper,
                    maintenance_sleeper,
                    general_error_sleeper
                ],
                'config': conf_mock.return_value
            }
            profile = kwargs.get('profile', 'default')
            conf_mock.assert_called_with(profile=profile)
            api_mock.assert_called_with(**called_with)


@pytest.mark.parametrize('project', [
    'user/project', mock.MagicMock(id='user/project', spec=Project)
])
def test_create_new_app(tool, project):
    with mock.patch('sbg.cwl.sbg.session.Api') as api_mock:
        project_mock = mock.MagicMock(id='user/project', spec=Project)

        session = Session(token='t', endpoint='e')

        session.api.apps.query.return_value = []
        session.api.projects.get.return_value = project_mock

        session.create_app(tool, project)
        session.api.apps.install_app.assert_called_with(
            id='{}/{}'.format(project_mock.id, tool.id), raw=tool
        )


@pytest.mark.parametrize('project', [
    'user/project', mock.MagicMock(id='user/project', spec=Project)
])
def test_create_app_no_changes(tool, project):
    with mock.patch('sbg.cwl.sbg.session.Api') as _:
        session = Session(token='t', endpoint='e')

        app_mock = mock.MagicMock()
        app_mock.raw = {'sbg:hash': tool.calc_hash()}
        session.api.apps.query.return_value = [app_mock]

        assert session.create_app(tool, project) == app_mock
        assert session.api.apps.create_revision.call_count == 0


@pytest.mark.parametrize('project', [
    'user/project', mock.MagicMock(id='user/project', spec=Project)
])
def test_create_app_new_revision(tool, project):
    with mock.patch('sbg.cwl.sbg.session.Api') as api_mock:
        project_mock = mock.MagicMock(id='user/project', spec=Project)

        session = Session(token='t', endpoint='e')

        app_mock = mock.MagicMock()
        old = cwl.CommandLineTool(id=tool.id, base_command=['echo', 'AAA'])
        app_mock.raw = {'sbg:hash': old.calc_hash()}
        app_mock.revision = 0

        session.api.apps.query.return_value = [app_mock]
        session.api.projects.get.return_value = project_mock

        assert session.create_app(tool, project) != app_mock
        session.api.apps.create_revision.assert_called_with(
            id='{}/{}'.format(project_mock.id, tool.id), raw=tool,
            revision=app_mock.revision + 1
        )


@pytest.mark.parametrize('hints', [
    [cwl.SaveLogs('v')], [cwl.MaxNumberOfParallelInstances(10)],
    [cwl.SbgFs(True)], [cwl.AwsHint('c4')],
    [cwl.SaveLogs('v'), cwl.MaxNumberOfParallelInstances(10),
     cwl.SbgFs(True), cwl.AwsHint('c4')]
])
def test_set_hints(tool, hints):
    tool = Session.add_hints(tool, *hints)
    assert tool.hints == hints


@pytest.mark.parametrize('project_id', ['user/project'])
@pytest.mark.parametrize('hints', [
    [cwl.SaveLogs('v')], [cwl.MaxNumberOfParallelInstances(10)],
    [cwl.SbgFs(True)], [cwl.AwsHint('c4')],
    [cwl.SaveLogs('v'), cwl.MaxNumberOfParallelInstances(10),
     cwl.SbgFs(True), cwl.AwsHint('c4')]
])
@pytest.mark.parametrize('inputs', [{}, {'file': 'path/to/file'}])
@mock.patch('sbg.cwl.sbg.session.Api', spec=Api)
def test_draft_task(api_mock, tool, project_id, hints, inputs):
    session = Session(token='t', endpoint='e')
    proj_mock = mock.MagicMock(spec=Project)

    session.api.apps.query.return_value = []
    session.api.projects.get.return_value = proj_mock
    session.draft(project_id, tool, inputs=inputs, hints=hints)

    app = Session.add_hints(tool, *hints)
    app = session.create_app(app, proj_mock)

    session.api.tasks.create.assert_called_with(
        mock.ANY, session.api.projects.get(project_id), app, inputs=inputs
    )
