from datetime import datetime
from sevenbridges.api import Api
from sevenbridges.config import Config
from sevenbridges.models.project import Project
from sbg.cwl.sbg.hints.hint import Hint
from sbg.cwl.v1_0.app import App as CwlApp
from sevenbridges.http.error_handlers import (
    general_error_sleeper, maintenance_sleeper, rate_limit_sleeper
)


class Session(object):

    def __init__(self, profile='default', endpoint=None, token=None, api=None):
        """
        Session for running CWL documents on SBG platform.

        :param profile: profile listed inside
                        ``$HOME/.sevenbridges/credentials``
                        (eg. cgc, default, cavatica)
        :param endpoint: api endpoint
        :param token: developer token from platform
        :param api: sbg api object

        Example:

        .. code-block:: python

           from sbg import cwl

           session = cwl.Session()  # default will be used
           session = cwl.Session(token='<DEV_TOKEN>', endpoint='<ENDPOINT>')
        """
        self.endpoint = endpoint
        self.token = token

        if api is not None:
            self.api = api
        else:
            self.api = Session.init_api(
                profile=profile, token=token, endpoint=endpoint
            )

    # region static
    @staticmethod
    def init_api(profile='default', token=None, endpoint=None):
        """
        Initialize SBG API using credentials located inside
        ``$HOME/.sevenbridges/credentials`` or by provided dev_token and
        platform.

        :param profile: profile listed inside
                        ``$HOME/.sevenbridges/credentials``.
                        Example: cgc, default, cavatica
        :param token: developer token from platform
        :param endpoint: api endpoint
        :return: an instance of ``Api``
        """

        if token and endpoint:
            api = Api(url=endpoint,
                      token=token,
                      error_handlers=[
                          rate_limit_sleeper,
                          maintenance_sleeper,
                          general_error_sleeper
                      ])
        else:
            c = Config(profile=profile)
            api = Api(config=c,
                      error_handlers=[
                          rate_limit_sleeper,
                          maintenance_sleeper,
                          general_error_sleeper
                      ])

        return api

    # endregion

    # region methods
    def create_app(self, app, project):
        """
        Install/create revision of app. New revision is created only if there
        is a difference from a latest revision.

        :param app: an instance of ``cwl.App``
        :param project: an instance of ``Project``
        :return: installed app

        Example:

        .. code-block:: python

           from sbg import cwl

           session = cwl.Session()
           session.create_app(
               app=cwl.CommandLineTool(id='my_id'),
               project='<PROJECT>'
           )
        """
        hash_key = 'sbg:hash'

        if not isinstance(project, Project):
            project = self.api.projects.get("{}".format(project))

        app_id = '{project}/{id}'.format(
            project=project.id,
            id=app.id
        )
        app_hash = app.calc_hash()
        result = self.api.apps.query(id=app_id)
        if len(result) == 0:  # install app
            app[hash_key] = app_hash
            app = self.api.apps.install_app(id=app_id, raw=app)
        else:  # create new revision if there are any changes
            sbg_app = result[0]
            sbg_app_hash = sbg_app.raw.get(hash_key)

            # hash values are equal => no changes
            if sbg_app_hash and app_hash == sbg_app_hash:
                app = sbg_app
            else:  # changes
                app[hash_key] = app_hash
                app = self.api.apps.create_revision(
                    id=app_id,
                    raw=app,
                    revision=result[0].revision + 1
                )
        return app

    def draft(self, project, app, inputs=None, hints=None):
        """
        Creates draft task.

        :param project: an instance of either ``Project`` or ``str``
        :param app: an instance of ``cwl.App``
        :param inputs: input map
        :param hints: SBG hints
        :return: created draft task

        Example:

        .. code-block:: python

           from sbg import cwl

           session = cwl.Session()
           session.draft(
               app=cwl.CommandLineTool(
                   id='my_id',
                   base_command=['echo', 'SevenBridges']
               ),
               project='<PROJECT>'
           )
        """
        if hints:
            app = Session.add_hints(app, *hints)

        if not inputs:
            inputs = {}

        if not isinstance(app, CwlApp):
            raise ValueError(
                'Required an instance of {}, got {}'.format(
                    CwlApp.__name__,
                    type(app)
                )
            )

        if not isinstance(project, Project):
            project = self.api.projects.get("{}".format(project))

        task_name = '{} - {}'.format(
            app.label if app.label else app.id,
            datetime.now().strftime('%Y.%m.%dT%H:%M:%S')
        )
        sbg_app = self.create_app(app, project)
        task = self.api.tasks.create(
            task_name, project, sbg_app, inputs=inputs
        )
        return task

    @staticmethod
    def add_hints(app, *hints):
        """
        Add hints on a ``app``.

        :param app: an instance of ``cwl.App``
        :param hints: hints
        :return: ``app`` with added hints
        """
        if hints:
            for h in hints:
                if isinstance(h, Hint):
                    if not app.hints:
                        app.hints = []
                    app.hints.append(h)
                else:
                    raise Exception('Expected Hint, got {}', type(h))
        return app

    def run(self, project, app, inputs=None, hints=None):
        """
        Runs ``app`` on a platform.

        :param project: an instance of either ``Project`` or ``str``
        :param app: an instance of ``cwl.App``
        :param inputs: input map
        :param hints: list of ``Hint``
        :return: task

        Example:

        .. code-block:: python

           from sbg import cwl

           session = cwl.Session()
           session.run(
               app=cwl.CommandLineTool(
                   id='my_id',
                   base_command=['echo', 'SevenBridges']
               ),
               project='<PROJECT>'
           )
        """
        task = self.draft(project, app, inputs=inputs, hints=hints)
        return task.run()
    # endregion
