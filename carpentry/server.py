#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
import logging

from tumbler.core import Web, MODULES
from flask import g, redirect, request
from carpentry import conf
from flask.ext.github import GitHub
from carpentry.models import User
from cqlengine import connection
from flask_socketio import SocketIO
from carpentry.registry import WEBSOCKET_HANDLERS

logger = logging.getLogger('carpentry')


class CarpentryHttpServer(Web):
    def __init__(self, log_level=logger.info, *args, **kw):
        super(CarpentryHttpServer, self).__init__(*args, **kw)
        setup_logging(log_level)

        self.flask_app.config.from_object('carpentry.conf')
        self.github = GitHub(self.flask_app)
        self.prepare_services_integration()

    def prepare_services_integration(self):
        self.setup_github_authentication()
        MODULES.clear()
        # self.collect_websocket_modules()
        self.collect_modules()

        connection.setup(conf.cassandra_hosts, default_keyspace='carpentry')

    def collect_websocket_modules(self):
        self.socket_io = SocketIO(self.flask_app)
        self.websockets = []
        for event, handler in WEBSOCKET_HANDLERS.items():
            register = self.socket_io.on(event)
            self.websockets.append(register(handler))

        return self.websockets

    def setup_github_authentication(self):

        @self.flask_app.before_request
        def prepare_user():
            carpentry_token = request.cookies.get('carpentry_token')
            g.user = User.from_carpentry_token(carpentry_token)

        @self.github.access_token_getter
        def token_getter():
            user = g.user
            if user is not None:
                return user.github_access_token

        @self.flask_app.route('/oauth/github.com')
        @self.github.authorized_handler
        def authorized(access_token):
            next_url = request.args.get('next') or conf.get_full_url('/')
            access_token = access_token or request.args.get('access_token')

            if access_token is None:
                logging.warning(
                    "No access token retrieved, set the log level "
                    "to debug and check flask-github's output. "
                    "You likely set the wrong github client id "
                    "and secret", access_token)
                return redirect(next_url)

            users = User.objects.filter(github_access_token=access_token)
            user_exists = len(users) > 0

            if not user_exists:
                g.user = User(
                    id=uuid.uuid1(),
                    carpentry_token=uuid.uuid4(),
                    github_access_token=access_token
                )
                logger.info("created new user", g.user)
            else:
                logger.info("User already exists with github_access_token %s %s", access_token, g.user)
                g.user = users[0]
                g.user.carpentry_token = uuid.uuid4()
                g.user.github_access_token = access_token

            g.user.save()

            logging.warning("authorized: %s - token: %s", g.user, access_token)

            response = redirect(next_url)
            response.set_cookie(
                'carpentry_token',
                bytes(g.user.carpentry_token),
            )
            return response

        @self.flask_app.route('/login', methods=["GET"])
        def login():
            response = self.github.authorize(scope='repo_deployment,repo,user,gist,write:repo_hook,repo:status,org:admin,admin:org_hook')
            return response

        @self.flask_app.route('/logout', methods=["GET"])
        def logout():
            response = redirect('/')
            if g.user:
                g.user.reset_token()

            response.set_cookie('carpentry_token', '', expires=0)
            return response


def setup_logging(level):
    LOG_HANDLERS = [
        'lineup.steps',
        'lineup',
        'tumbler',
        'carpentry',
    ]

    WARNING_ONLY_HANDLERS = [
        'cqlengine.cql',
        'werkzeug',
        'requests.packages.urllib3.connectionpool',
        'cassandra.io.asyncorereactor'
    ]

    for name in WARNING_ONLY_HANDLERS:
        logger = logging.getLogger(name)
        logger.setLevel(logging.WARNING)

    for name in LOG_HANDLERS:
        logger = logging.getLogger(name)
        logger.setLevel(level)
