#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from __future__ import unicode_literals
import types
import uuid
import logging
import inspect

from flask import request
from tumbler import json_response
from Crypto.PublicKey import RSA
from carpentry import conf
from carpentry.api.core import (
    authenticated,
    ensure_json_request
)
from carpentry.models import CarpentryBaseActiveRecord
from carpentry.util import get_docker_client

from carpentry import models

from carpentry.api import web
from ansi2html import Ansi2HTMLConverter
from repocket import configure


pool = configure.connection_pool(
    hostname='localhost',
    port=6379
)

connection = pool.get_connection()

conv = Ansi2HTMLConverter()

TIMEOUT_BEFORE_SIGKILL = 5  # seconds


def is_model(v):
    return (
        isinstance(v, type) and
        issubclass(v, CarpentryBaseActiveRecord) and
        v != CarpentryBaseActiveRecord
    )


def get_models():
    return [v for (k, v) in inspect.getmembers(models) if is_model(v)]


logger = logging.getLogger('carpentry.resources')


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
        b = models.Build.objects.get(id=id)
    except Exception as e:
        return json_response({'error': str(e)}, status=404)

    data = b.builder.to_dictionary()
    data.update(b.to_dictionary())

    return json_response(data)


@web.post('/api/builder')
@authenticated
def create_builder(user):
    data = ensure_json_request({
        'name': unicode,
        'git_uri': unicode,
        'shell_script': unicode,
        'json_instructions': any,
        'id_rsa_private': any,
        'generate_ssh_keys': bool,
        'id_rsa_public': any,
    })
    data['id'] = uuid.uuid1()
    data['creator'] = user
    data['status'] = 'ready'
    should_generate_ssh_keys = data.pop('generate_ssh_keys')

    if should_generate_ssh_keys:
        private_key, public_key = generate_ssh_key_pair(2048)
        data['id_rsa_private'] = private_key
        data['id_rsa_public'] = public_key

    builder = models.Builder.create(**data)
    logger.info('creating new builder: %s', builder.name)
    builder.cleanup_github_hooks()

    hook = builder.set_github_hook(user.github_access_token)

    logger.info('setting github hook: %s', hook)

    payload = builder.to_dictionary()
    return json_response(payload, status=200)


@web.get('/api/builder/<id>')
@authenticated
def retrieve_builder(user, id):
    item = models.Builder.objects.get(id=id)
    logger.info('show builder: %s', item.name)
    return json_response(item.to_dictionary())


@web.delete('/api/builder/<id>/builds')
@authenticated
def clear_builds(user, id):
    builder = models.Builder.objects.get(id=id)
    deleted_builds = builder.clear_builds()
    if not deleted_builds:
        return json_response({'total': 0})

    builder.status = 'ready'
    builder.save()
    total = len(deleted_builds)
    logging.info("Deleted {0} builds of commits {2}:\n{1}".format(
        total,
        "\n".join(filter(bool, [b.commit for b in deleted_builds if b])),
        builder.git_uri
    ))
    return json_response({'total': total})


@web.get('/api/builder/<id>/builds')
@authenticated
def builds_from_builder(user, id):
    builder = models.Builder.objects.get(id=id)
    items = builder.get_all_builds()
    return json_response([item.to_dictionary() for item in items])


@web.put('/api/builder/<id>')
@authenticated
def edit_builder(user, id):
    data = ensure_json_request({
        'name': any,
        'git_uri': any,
        'shell_script': any,
        'json_instructions': any,
        'id_rsa_public': any,
        'id_rsa_private': any,
    })
    item = models.Builder.objects.get(id=id)
    for attr, value in data.items():
        if value:
            item.set(attr, value)

    item.save()

    item.cleanup_github_hooks(user.github_access_token)
    item.set_github_hook(user.github_access_token)

    logger.info('edit builder: %s', item.name)
    return json_response(item.to_dictionary())


@web.delete('/api/builder/<id>')
@authenticated
def remove_builder(user, id):
    item = models.Builder.objects.get(id=id)
    item.clear_builds()
    item.cleanup_github_hooks(user.github_access_token)

    item.delete()
    logger.info('deleting builder: %s', item.name)
    return json_response(item.to_dictionary())


@web.delete('/api/build/<id>')
@authenticated
def remove_build(user, id):
    item = models.Build.objects.get(id=id)
    item.delete()
    logger.info('deleting build: %s', item.name)
    return json_response(item.to_dictionary())


@web.get('/api/builders')
@authenticated
def list_builders(user):
    items = [b.to_dictionary() for b in models.Builder.objects.all()]
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
    valid_base_types = types.StringTypes + (types.DictionaryType, types.ListType, types.TupleType, types.NoneType, types.IntType)
    data = dict([(attr, getattr(conf, attr)) for attr in dir(conf)])
    return json_response(
        dict([(k, v) for k, v in data.items() if isinstance(v, valid_base_types) and not k.startswith('_')]))


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
    return json_response(item.to_dictionary())


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

    user = item.creator
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
    return json_response(build.to_dictionary())


@web.get('/api/docker/images')
@authenticated
def list_images(user):
    docker = get_docker_client()
    data = sorted(docker.images(), key=lambda x: x['Id'])
    return json_response(data)


@web.get('/api/docker/containers')
@authenticated
def list_containers(user):
    docker = get_docker_client()
    data = sorted(docker.containers(all=True), key=lambda x: x['Id'])
    return json_response(data)


@web.post('/api/docker/container/<container_id>/stop')
@authenticated
def stop_container(user, container_id):
    docker = get_docker_client()

    data = docker.stop(
        container_id,
        TIMEOUT_BEFORE_SIGKILL
    )
    return json_response(data)


@web.post('/api/docker/container/<container_id>/remove')
@authenticated
def remove_container(user, container_id):
    docker = get_docker_client()

    data = docker.remove_container(
        container_id,
        v=True,
    )
    return json_response(data)


@web.post('/api/docker/image/<image_id>/remove')
@authenticated
def remove_image(user, image_id):
    docker = get_docker_client()

    data = docker.remove_image(
        image_id,
        force=True,
        noprune=False
    )
    return json_response(data)


@web.get('/api/github/repos')
@authenticated
def get_github_repos(user):
    results = user.retrieve_and_cache_github_repositories()
    return json_response(results)
