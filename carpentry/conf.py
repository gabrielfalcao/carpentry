#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import urlparse
from plant import Node
from milieu import Environment

self = sys.modules[__name__]
DEFAULT_WORKDIR = os.getenv('CARPENTRY_WORKDIR') or '/tmp/carpentry'


def get_env(path):
    if os.path.exists(path):
        env = Environment.from_file(path)
    else:
        env = Environment()
    return env


def set_things(self, env):
    self.redis_host = env.get('redis_host', 'localhost')
    self.redis_port = env.get_int('redis_port', 6379)
    self.redis_db = env.get_int('redis_db', 0)
    self.cassandra_hosts = env.get('cassandra_hosts')

    self.workdir = env.get('workdir', DEFAULT_WORKDIR)
    self.full_server_url = env.get('full_server_url')
    self.hostname = env.get('http_host')
    self.port = env.get('http_port')

    self.workdir_node = Node(self.workdir)
    self.build_node = self.workdir_node.cd('builds')
    self.ssh_keys_node = self.workdir_node.cd('ssh-keys')
    self.GITHUB_CLIENT_ID = env.get('github_client_id')
    self.GITHUB_CLIENT_SECRET = env.get('github_client_secret')
    self.allowed_github_organizations = env.get('allowed_github_organizations', ['cnry'])
    self.SECRET_KEY = env.get('secret_key')

    self.default_subprocess_timeout_in_seconds = env.get('default_subprocess_timeout_in_seconds', 60 * 10)

    self.git_executable_path = env.get('git_executable_path', '/usr/bin/git')
    self.ssh_executable_path = env.get('ssh_executable_path', '/usr/bin/ssh')

    self.get_full_url = lambda path: urlparse.urljoin(self.full_server_url, path)


def setup_from_config_path(self, path):
    env = get_env(path)
    set_things(self, env)


carpentry_config_path = os.getenv('CARPENTRY_CONFIG_PATH') or '/etc/carpentry.yml'
setup_from_config_path(self, carpentry_config_path)
