#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import uuid
from sure import scenario

from tumbler.core import Web
from cqlengine import connection
from cqlengine.management import sync_table, drop_table, create_keyspace
from carpentry.api.resources import get_models
from carpentry.models import User, get_pipeline
from carpentry import conf


def prepare_db(context):
    # CREATE KEYSPACE carpentry
    #        WITH REPLICATION =
    #                { 'class' : 'SimpleStrategy', 'replication_factor' : 3 };
    connection.setup(conf.cassandra_hosts, default_keyspace='carpentry')
    create_keyspace('carpentry', strategy_class='SimpleStrategy', replication_factor=3, durable_writes=True)

    for t in get_models():
        try:
            drop_table(t)
            sync_table(t)
        except Exception:
            logging.exception('Failed to drop/sync %s', t)


def prepare_http_client(context):
    context.web = Web()
    context.http = context.web.flask_app.test_client()
    context.user = User(id=uuid.uuid1(), carpentry_token=uuid.uuid4())
    context.user.save()
    context.headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer: {0}'.format(context.user.carpentry_token)
    }


def clean_db(context):
    redis = get_pipeline().get_backend().redis
    redis.flushall()
    for t in get_models():
        sync_table(t)

safe_db = scenario(prepare_db, clean_db)
api = scenario([prepare_db, prepare_http_client], [clean_db])
