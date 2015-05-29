#!/usr/bin/env python
# -*- coding: utf-8 -*-
# flake8: noqa

import logging
from sure import scenario

from tumbler.core import Web
from jaci.models import Builder
from cqlengine import connection
from cqlengine.management import sync_table, drop_table, create_keyspace
from jaci.api.v1 import web


def prepare_db(context):
    # CREATE KEYSPACE jaci
    #        WITH REPLICATION =
    #                { 'class' : 'SimpleStrategy', 'replication_factor' : 3 };
    context.connection = connection.setup(['127.0.0.1'], 'jaci')
    create_keyspace('jaci', strategy_class='SimpleStrategy', replication_factor=3, durable_writes=True)
    tables = [Builder, ]
    for t in tables:
        try:
            drop_table(t)
            sync_table(t)
        except Exception:
            logging.exception('Failed to drop/sync %s', t)


def prepare_http_client(context):
    context.web = Web()
    context.http = context.web.flask_app.test_client()
    context.headers = {
        'Content-Type': 'application/json',
    }


def clean_db(context):
    sync_table(Builder)


safe_db = scenario(prepare_db, clean_db)
api = scenario([prepare_db, prepare_http_client], [clean_db])
