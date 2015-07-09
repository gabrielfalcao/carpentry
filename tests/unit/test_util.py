#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
from mock import patch, Mock
from carpentry.util import get_docker_client
from carpentry.conf import get_env


@patch('carpentry.util.kwargs_from_env')
@patch('carpentry.util.Client')
def test_get_docker_client(Client, kwargs_from_env):
    ('carpentry.util.get_docker_client() returns a client instance using kwargs_from_env')

    tls = Mock(name='DockerTLS')
    tls.verify = True

    kwargs_from_env.return_value = {
        'can': 'ary',
        'tls': tls,
    }

    result = get_docker_client()

    result.should.equal(Client.return_value)


@patch('carpentry.conf.os')
@patch('carpentry.conf.Environment')
def test_get_env_fallsback_to_empty_milieu(Environment, os):
    ('carpentry.conf.get_env() should fall back to an empty milieu.Environment() when the given path does not exit')

    os.path.exists.return_value = False
    get_env('/fake').should.equal(
        Environment.return_value)


@patch('carpentry.conf.os')
@patch('carpentry.conf.Environment')
def test_get_env(Environment, os):
    ('carpentry.conf.get_env() returns an Environment.from_file')

    os.path.exists.return_value = True
    get_env('/yay').should.equal(
        Environment.from_file.return_value)
