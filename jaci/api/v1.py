#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import uuid
import logging
from dateutil.parser import parse as parse_datetime
from tumbler import tumbler
from tumbler import json_response

web = tumbler.module(__name__)

# from jaci.models import Builder
from jaci.api.core import authenticated, ensure_json_request
from jaci.models import Builder


def autodatetime(s):
    return s and parse_datetime(s) or None


@web.post('/api/builder')
@authenticated
def create_builder(user):
    data = ensure_json_request({
        'name': unicode,
        'git_url': unicode,
        'shell_script': unicode,
        'id_rsa_private': any,
        'id_rsa_public': any,
        'status': any,
    })
    data['id'] = uuid.uuid1()
    builder = Builder.create(**data)
    logging.info('creating new builder: %s', builder.name)

    return json_response(builder.to_dict())


@web.get('/api/builders/latest')
def latest_builders():
    builders = Builder.objects.all()
    results = [p.to_dict() for p in builders]
    return json_response(results)
