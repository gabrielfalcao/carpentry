#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2013 Gabriel Falcão <gabriel@jaci.com>
#
from __future__ import unicode_literals
import io
import sh
from plant import Node
import logging
import subprocess
from jaci.api.v1 import web
from tumbler import json_response
# from jaci.api.core import authenticated

from flask import Response, render_template
from ansi2html import Ansi2HTMLConverter

conv = Ansi2HTMLConverter()


@web.get('/')
def index():
    logging.debug("serving index")
    return render_template("index.html")


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
    logging.debug("serving app.js: %skb", len(joined) / 1000.0)
    return Response(joined, status=200, headers={
        'Content-Type': 'text/javascript'
    })


@web.get('/build')
def get_build_output():
    stdout = sh.find(".")
    return json_response({
        'stdout': conv.convert(stdout, full=False)
    })
