#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2013 Gabriel Falcão <gabriel@jaci.com>
#
from __future__ import unicode_literals

import io

from plant import Node
import logging

from jaci.api.v1 import web
# from jaci.api.core import authenticated

from flask import Response, render_template, request


@web.get('/')
def index():
    logging.info("serving index")
    return render_template("index.html", **{
        'user_token': request.cookies.get('jaci_token') or ''
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
