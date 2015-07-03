#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals

import warnings
from docker import Client
from docker.utils import kwargs_from_env


warnings.simplefilter("ignore")


def render_string(template, context):
    return template.format(**context)


def get_docker_client():
    kwargs = kwargs_from_env()
    if 'tls' in kwargs:
        kwargs['tls'].verify = False

    kwargs['timeout'] = 60 * 5

    docker = Client(**kwargs)
    return docker
