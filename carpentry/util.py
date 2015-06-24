#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals


def render_string(template, context):
    return template.format(**context)


def calculate_redis_key(instructions):
    out_key = render_string('carpentry:stdout:{id}', instructions)
    err_key = render_string('carpentry:stderr:{id}', instructions)
    return out_key, err_key
