#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2013 Gabriel Falcão <gabriel@carpentry.com>
#
from __future__ import unicode_literals

import io
import time
import mimetypes
import logging

from plant import Node
from flask import Response, render_template, request

from carpentry import conf
from carpentry.api.v1 import web
from carpentry.version import version as carpentry_version


this_node = Node(__file__).dir
mimedb = mimetypes.MimeTypes()


@web.get('/')
def index():
    logging.info("serving index")
    return render_template("index.html", **{
        'cache_flag': '-'.join([carpentry_version, str(time.time())]),
        'absolute_url': conf.get_full_url,
        'user_token': request.cookies.get('carpentry_token') or ''
    })


def get_js_nodes():
    this_node = Node(__file__).dir
    js_node = this_node.cd('static/js')
    return js_node.glob('*.js')


def get_all_js():
    parts = []
    for node in get_js_nodes():
        read = io.open(node.path).read()
        parts.append(read)

    joined = ';'.join(parts)
    return joined


@web.get('/app.js')
def app_js():
    joined = get_all_js()
    logging.info("serving app.js: %skb", len(joined) / 1000.0)
    return Response(joined, status=200, headers={
        'Content-Type': 'text/javascript'
    })


# @web.get('/assets/<path:path>')
# def assets(path):
#     local_path = this_node.cd('static').join(path)
#     with io.open(local_path) as fd:
#         joined = fd.read()

#     logging.info("serving %s: %skb", path, len(joined) / 1000.0)
#     return Response(joined, status=200, headers={
#         'Content-Type': mimetypes.guess_type(path)
#     })
