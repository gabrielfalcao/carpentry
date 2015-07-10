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
from carpentry.api.core import (
    authenticated,
    ensure_json_request
)
from carpentry.models import CarpentryBaseModel
from carpentry.util import get_docker_client

from carpentry import models

from carpentry.api import web
from ansi2html import Ansi2HTMLConverter


conv = Ansi2HTMLConverter()

TIMEOUT_BEFORE_SIGKILL = 5  # seconds


def is_model(v):
    return (
        isinstance(v, type) and
        issubclass(v, CarpentryBaseModel) and
        v != CarpentryBaseModel
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
        'json_instructions': any,
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

    builder = models.Builder.create(**data)
    logger.info('creating new builder: %s', builder.name)
    builder.cleanup_github_hooks()

    hook = builder.set_github_hook(user.github_access_token)

    logger.info('setting github hook: %s', hook)

    payload = builder.to_dict()
    return json_response(payload, status=200)


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
    if not deleted_builds:
        return json_response({'total': 0})

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
    item.set_github_hook(user.github_access_token)

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


@web.post('/api/docker/pull')
@authenticated
def docker_pull(user):
    docker = get_docker_client()
    data = ensure_json_request({
        'repository': unicode,
        'tag': any,
    })
    repository = data['repository']
    tag = data.get('tag', 'latest')
    data = docker.pull(repository, tag)
    return json_response(data)


@web.post('/api/docker/run')
@authenticated
def docker_run(user, image_id):
    docker = get_docker_client()
    data = ensure_json_request({
        'imageName': unicode,
        'hostname': unicode,
    })
    image_name = data['imageName']
    hostname = data['hostname']

    container = docker.create_container(
        image=image_name,
        name=hostname,
        detach=True,
        hostname=hostname)

    docker.start(container['Id'])

    return json_response(dict(container))


@web.get('/api/github/repos')
@authenticated
def get_github_repos(user):
    results = user.retrieve_and_cache_github_repositories()
    return json_response(results)
