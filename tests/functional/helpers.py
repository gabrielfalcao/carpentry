#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from sure import scenario

from tumbler.core import Web

from cqlengine.management import sync_table, drop_table, create_keyspace
from jaci.api.v1 import get_models


def prepare_db(context):
    # CREATE KEYSPACE jaci
    #        WITH REPLICATION =
    #                { 'class' : 'SimpleStrategy', 'replication_factor' : 3 };
    create_keyspace('jaci', strategy_class='SimpleStrategy', replication_factor=3, durable_writes=True)

    for t in get_models():
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
    for t in get_models():
        sync_table(t)

safe_db = scenario(prepare_db, clean_db)
api = scenario([prepare_db, prepare_http_client], [clean_db])
