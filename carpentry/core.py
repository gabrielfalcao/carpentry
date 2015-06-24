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

LOGHANDLERS = ['lineup.steps', 'lineup', 'tumbler', 'carpentry']


class CarpentryHttpServer(Web):
    def __init__(self, log_level=logging.INFO, *args, **kw):
        super(CarpentryHttpServer, self).__init__(*args, **kw)
        self.flask_app.config.from_object('carpentry.conf')
        self.github = GitHub(self.flask_app)
        self.setup_github_authentication()
        MODULES.clear()
        self.collect_modules()
        setup_logging(log_level)
        connection.setup(conf.cassandra_hosts, default_keyspace='carpentry')

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
            else:
                g.user = users[0]
                g.user.carpentry_token = uuid.uuid4()
                g.user.github_access_token = access_token

            g.user.save()

            logging.warning("authorized: %s", g.user)

            response = redirect(next_url)
            response.set_cookie('carpentry_token', bytes(g.user.carpentry_token))
            return response

        @self.flask_app.route('/login', methods=["GET"])
        def login():
            response = self.github.authorize(scope='repo_deployment,repo,user,gist,write:repo_hook')
            response.set_cookie('carpentry_token', '', expires=0)
            return response

        @self.flask_app.route('/logout', methods=["GET"])
        def logout():
            response = redirect('/')
            if g.user:
                g.user.reset_token()

            response.set_cookie('carpentry_token', '', expires=0)
            return response


def setup_logging(level):
    logging.getLogger('cqlengine.cql').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    for name in LOGHANDLERS:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
