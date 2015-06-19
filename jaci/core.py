#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
import logging
from tumbler.core import Web
from flask import g, redirect, request, session
from flask.ext.github import GitHub
from jaci.models import User

LOGHANDLERS = ['lineup.steps', 'lineup', 'tumbler', 'jaci']


class JaciHttpServer(Web):
    def __init__(self, log_level=logging.INFO, *args, **kw):
        super(JaciHttpServer, self).__init__(*args, **kw)
        self.flask_app.config.from_object('jaci.conf')
        self.github = GitHub(self.flask_app)
        self.setup_github_authentication()
        setup_logging(log_level)

    def setup_github_authentication(self):
        @self.github.access_token_getter
        def token_getter():
            user = g.user
            if user is not None:
                return user.github_access_token

        @self.flask_app.route('/oauth/github.com')
        @self.github.authorized_handler
        def authorized(access_token):
            next_url = request.args.get('next') or '/'
            access_token = access_token or request.args.get('access_token')

            logging.warning("authorized_handler token: %s", access_token)
            if access_token is None:
                return redirect(next_url)

            users = User.objects.filter(github_access_token=access_token)
            user_exists = len(users) > 0

            if not user_exists:
                g.user = User(
                    id=uuid.uuid1(),
                    jaci_token=uuid.uuid4(),
                )
            else:
                g.user = users[0]
                g.user.jaci_token = uuid.uuid4()

            g.user.save()
            session['user_id'] = g.user.id
            session['jaci_token'] = g.user.jaci_token
            session['github_access_token'] = access_token
            return redirect('/')

        @self.flask_app.route('/login', methods=["GET"])
        def login():
            return self.github.authorize()


def setup_logging(level):
    logging.getLogger('cqlengine.cql').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    for name in LOGHANDLERS:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
