#!/usr/bin/env python
# -*- coding: utf-8 -*-
import httpretty

import uuid
import json
from sure import scenario

from tumbler.core import Web
from repocket import configure

from carpentry.models import User


class GithubMocker(object):

    def __init__(self, user):
        self.user = user

    def on_post(self, path, body=None, status=200, headers={}):
        httpretty.register_uri(
            httpretty.POST,
            "/".join(["https://api.github.com", path.lstrip('/')]),
            body=body,
            headers=headers,
            status=status
        )

    def on_get(self, path, body=None, status=200, headers={}):
        url = "/".join(["https://api.github.com", path.lstrip('/')])
        httpretty.register_uri(
            httpretty.GET,
            url,
            body=body,
            headers=headers,
            status=status
        )

    def on_put(self, path, body=None, status=200, headers={}):
        httpretty.register_uri(
            httpretty.PUT,
            "/".join(["https://api.github.com", path.lstrip('/')]),
            body=body,
            headers=headers,
            status=status
        )

    def on_delete(self, path, body=None, status=200, headers={}):
        httpretty.register_uri(
            httpretty.DELETE,
            r"/".join([r"https://api.github.com", path.lstrip('/')]),
            body=body,
            headers=headers,
            status=status
        )


def prepare_redis(context):
    context.pool = configure.connection_pool(
        hostname='localhost',
        port=6379
    )
    context.connection = context.pool.get_connection()
    sweep_redis(context)


def sweep_redis(context):
    context.connection.flushall()


def prepare_http_client(context):
    context.web = Web()
    context.http = context.web.flask_app.test_client()
    context.user = User(id=uuid.uuid1(), carpentry_token=uuid.uuid4(
    ), github_access_token='Default:FAKE:Token')
    context.user.save()

    context.github = GithubMocker(context.user)
    context.github.on_get('/user/orgs', body=json.dumps([
        {
            'login': 'cnry'
        }
    ]))

    context.headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer: {0}'.format(context.user.carpentry_token)
    }


safe_db = scenario(prepare_redis, sweep_redis)
api = scenario([prepare_redis, prepare_http_client], [sweep_redis])
