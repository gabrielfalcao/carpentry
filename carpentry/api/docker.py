#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals

from carpentry.api import web
from tumbler import json_response
from docker.utils import create_host_config
from carpentry.util import get_docker_client
from carpentry.api.core import authenticated
# from carpentry.api.core import ensure_json_request


@web.get('/api/docker/images')
@authenticated
def list_images(user):
    docker = get_docker_client()
    data = docker.images()
    return json_response(data)


@web.get('/api/docker/containers')
@authenticated
def list_containers(user):
    docker = get_docker_client()
    data = docker.containers(all=True)
    return json_response(data)
