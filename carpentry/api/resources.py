#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import uuid
import logging
import inspect
from dateutil.parser import parse as parse_datetime
from flask import request
from tumbler import json_response
from Crypto.PublicKey import RSA
from carpentry import conf
from carpentry.api.core import authenticated, ensure_json_request
from cqlengine.models import Model

from carpentry import models

from carpentry.api import web
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

logger = logging.getLogger('carpentry')


def generate_ssh_key_pair(length=2048):
    private_key = RSA.generate(2048)
    public_key = private_key.publickey()

    private_string = private_key.exportKey('PEM')
    public_string = public_key.exportKey('OpenSSH')
    return private_string, public_string


@web.get('/api/build/<id>')
@authenticated
def get_build(user, id):
    try:
        b = models.Build.get(id=id)
    except Exception as e:
        return json_response({'error': str(e)}, status=400)

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
        'generate_ssh_keys': bool,
        'id_rsa_public': any,
        'status': any,
    })
    data['id'] = uuid.uuid1()
    data['creator_user_id'] = user.id
    should_generate_ssh_keys = data.pop('generate_ssh_keys')

    if should_generate_ssh_keys:
        private_key, public_key = generate_ssh_key_pair(2048)
        data['id_rsa_private'] = private_key
        data['id_rsa_public'] = public_key

    try:
        builder = models.Builder.create(**data)
        logger.info('creating new builder: %s', builder.name)

        hook = builder.set_github_hook(user.github_access_token)
        logger.info('setting github hook: %s', hook)

        builder.cleanup_github_hooks()
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


@web.delete('/api/builder/<id>/builds')
@authenticated
def clear_builds(user, id):
    builder = models.Builder.get(id=id)
    deleted_builds = builder.clear_builds()
    total = len(deleted_builds)
    logging.info("Deleted {0} builds of commits {2}:\n{1}".format(
        total,
        "\n".join([b.commit for b in deleted_builds if b]),
        builder.git_uri
    ))
    return json_response({'total': total})


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
    item.cleanup_github_hooks(user.github_access_token)
    logger.info('edit builder: %s', item.name)
    return json_response(item.to_dict())


@web.delete('/api/builder/<id>')
@authenticated
def remove_builder(user, id):
    item = models.Builder.objects.get(id=id)
    item.clear_builds()
    item.cleanup_github_hooks(user.github_access_token)
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
        preferences = models.CarpentryPreference.create(**data)
        results[key] = value
        logger.info('setting preference %s: %s', key, value)

    return json_response(results)


@web.get('/api/conf')
@authenticated
def get_conf(user):
    return json_response(dict([(attr, getattr(conf, attr)) for attr in dir(conf)]))


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
    item = builder.trigger(user, branch=builder.branch, **data)
    return json_response(item.to_dict())


@web.get('/api/user')
@authenticated
def get_user(user):
    return json_response(user.get_github_metadata(), status=200)


@web.post('/api/hooks/<id>')
def trigger_builder_hook(id):
    try:
        item = models.Builder.objects.get(id=id)
    except Exception:
        logger.exception("Failed to retrieve builder of id: %s", id)
        return json_response({}, status=404)

    user = models.User.get(id=item.creator_user_id)
    logger.info('triggering build for: %s', item.git_uri)
    request_data = request.get_json(silent=True) or {}
    head_commit = request_data.get('head_commit', {})
    commit_id = head_commit.get('id', None)
    commiter = head_commit.get('commiter', {})
    author_name = commiter.get('name', user.name)
    author_email = commiter.get('email', user.email)

    repo = request_data.get('repository', {})
    branch = repo.get('master_branch', None)

    build = item.trigger(
        user,
        branch=branch or 'master',
        commit=commit_id,
        author_name=author_name,
        author_email=author_email,
        github_webhook_data=request.data
    )
    return json_response(build.to_dict())
