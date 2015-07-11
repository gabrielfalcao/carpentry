#!/usr/bin/env python
# -*- coding: utf-8 -*-
import httpretty
import logging
import uuid
import json
from sure import scenario

from tumbler.core import Web
from cqlengine import connection
from cqlengine.management import sync_table, drop_table, create_keyspace
from carpentry.api.resources import get_models
from carpentry.models import User, get_pipeline
from carpentry import conf


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


def prepare_db(context):
    # CREATE KEYSPACE carpentry
    #        WITH REPLICATION =
    #                { 'class' : 'SimpleStrategy', 'replication_factor' : 3 };
    connection.setup(conf.cassandra_hosts, default_keyspace='carpentry')
    create_keyspace('carpentry', strategy_class='SimpleStrategy',
                    replication_factor=3, durable_writes=True)
    httpretty.enable()

    for t in get_models():
        try:
            drop_table(t)
            sync_table(t)
        except Exception:
            logging.exception('Failed to drop/sync %s', t)


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


def clean_db(context):
    redis = get_pipeline().get_backend().redis
    redis.flushall()
    httpretty.disable()
    httpretty.reset()

    for t in get_models():
        sync_table(t)

safe_db = scenario(prepare_db, clean_db)
api = scenario([prepare_db, prepare_http_client], [clean_db])
