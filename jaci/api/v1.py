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
from jaci.models import Builder, JaciPreference


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


@web.put('/api/builder/<id>')
@authenticated
def edit_builder(user, id):
    data = ensure_json_request({
        'name': any,
        'git_url': any,
        'shell_script': any,
        'id_rsa_private': any,
        'id_rsa_public': any,
        'status': any,
    })
    item = Builder.objects.get(id=id)
    for attr, value in data.items():
        if value is None:
            continue
        setattr(item, attr, value)

    item.save()
    logging.info('edit builder: %s', item.name)
    return json_response(item.to_dict())


@web.delete('/api/builder/<id>')
@authenticated
def remove_builder(user, id):
    item = Builder.objects.get(id=id)
    item.delete()
    logging.info('deleting builder: %s', item.name)
    return json_response(item.to_dict())


@web.get('/api/builders')
@authenticated
def list_builders(user):
    items = [b.to_dict() for b in Builder.objects.all()]
    return json_response(items)


@web.post('/api/preferences')
@authenticated
def set_preferences(user):
    preferences = ensure_json_request({
        'global_id_rsa_private_key': any,
        'global_id_rsa_public_key': any,
        'docker_registry_url': any,
    })
    results = {}
    for key, value in preferences.items():
        if not value:
            logging.info('skipping None key: %s', key)
            continue

        data = {
            'id': uuid.uuid1(),
            'key': key,
            'value': value
        }
        preferences = JaciPreference.create(**data)
        results[key] = value
        logging.info('setting preference %s: %s', key, value)

    return json_response(results)


@web.post('/api/builder/<id>/build')
@authenticated
def create_build(user, id):
    builder = Builder.objects.get(id=id)
    item = builder.trigger(builder.branch)
    return json_response(item.to_dict())
