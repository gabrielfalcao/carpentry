#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import uuid
import logging
import inspect
from dateutil.parser import parse as parse_datetime
from tumbler import tumbler
from tumbler import json_response

web = tumbler.module(__name__)

# from jaci.models import Builder
from jaci.api.core import authenticated, ensure_json_request
from cqlengine.models import Model

from jaci import models
from jaci.util import calculate_redis_key
from ansi2html import Ansi2HTMLConverter

conv = Ansi2HTMLConverter()


def is_model(v):
    return (
        isinstance(v, type) and
        issubclass(v, Model) and
        v != Model
    )


def get_models():
    return [v for (k, v) in inspect.getmembers(models) if is_model(v)]


def autodatetime(s):
    return s and parse_datetime(s) or None

logger = logging.getLogger('werkzeug')


@web.get('/api/build/<id>/output')
@authenticated
def get_build_output(user, id):
    partial_instructions = {'id': id}
    pipeline = models.get_pipeline()
    backend = pipeline.get_backend()
    out_key, err_key = calculate_redis_key(partial_instructions)

    stdout = backend.redis.get(out_key) or 'waiting for workers...'
    # stderr = backend.redis.get(err_key) or ''

    return json_response({
        'stdout': conv.convert(stdout, full=False),
    })


@web.get('/api/build/<id>')
@authenticated
def get_build(user, id):
    b = models.Build.get(id=id)
    builder = models.Builder.get(id=b.builder_id)

    data = builder.to_dict()
    data.update(b.to_dict())

    return json_response(data)


@web.post('/api/builder')
@authenticated
def create_builder(user):
    data = ensure_json_request({
        'name': unicode,
        'git_uri': unicode,
        'shell_script': unicode,
        'id_rsa_private': any,
        'id_rsa_public': any,
        'status': any,
    })
    data['id'] = uuid.uuid1()

    try:
        builder = models.Builder.create(**data)
        logger.info('creating new builder: %s', builder.name)

        payload = builder.to_dict()
        return json_response(payload, status=200)

    except Exception as e:
        logger.exception('Failed to create builder')
        payload = {'error': unicode(e)}
    return json_response(payload, status=500)


@web.get('/api/builder/<id>')
@authenticated
def retrieve_builder(user, id):
    item = models.Builder.objects.get(id=id)
    logger.info('show builder: %s', item.name)
    return json_response(item.to_dict())


@web.get('/api/builder/<id>/builds')
@authenticated
def builds_from_builder(user, id):
    items = models.Build.objects.filter(builder_id=id)
    return json_response([item.to_dict() for item in items])


@web.put('/api/builder/<id>')
@authenticated
def edit_builder(user, id):
    data = ensure_json_request({
        'name': any,
        'git_uri': any,
        'shell_script': any,
        'id_rsa_private': any,
        'id_rsa_public': any,
    })
    item = models.Builder.objects.get(id=id)
    for attr, value in data.items():
        if value is None:
            continue
        setattr(item, attr, value)

    item.save()
    logger.info('edit builder: %s', item.name)
    return json_response(item.to_dict())


@web.delete('/api/builder/<id>')
@authenticated
def remove_builder(user, id):
    item = models.Builder.objects.get(id=id)
    item.delete()
    logger.info('deleting builder: %s', item.name)
    return json_response(item.to_dict())


@web.get('/api/builders')
@authenticated
def list_builders(user):
    items = [b.to_dict() for b in models.Builder.objects.all()]
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
            logger.info('skipping None key: %s', key)
            continue

        data = {
            'id': uuid.uuid1(),
            'key': key,
            'value': value
        }
        preferences = models.JaciPreference.create(**data)
        results[key] = value
        logger.info('setting preference %s: %s', key, value)

    return json_response(results)


@web.post('/api/builder/<id>/build')
@authenticated
def create_build(user, id):
    data = ensure_json_request(
        {
            'author_name': any,
            'author_email': any,
        },
        {
            'author_name': user.name,
            'author_email': user.email,

        }
    )

    builder = models.Builder.objects.get(id=id)
    item = builder.trigger(builder.branch, **data)
    return json_response(item.to_dict())
