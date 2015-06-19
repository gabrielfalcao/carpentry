#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
from plant import Node
from milieu import Environment

self = sys.modules[__name__]
DEFAULT_WORKDIR = os.getenv('JACI_WORKDIR') or '/srv/jaci'


def get_env(self, path):
    if os.path.exists(jaci_config_path):  # pragma: no cover
        env = Environment.from_file(jaci_config_path)
    else:
        env = Environment()
    return env


def set_things(self, env):
    self.redis_host = env.get('redis_host', 'localhost')
    self.redis_port = env.get_int('redis_port', 6379)
    self.redis_db = env.get_int('redis_db', 0)
    self.cassandra_hosts = env.get('cassandra_hosts')
    self.workdir = env.get('workdir', DEFAULT_WORKDIR)
    self.node = Node(self.workdir)


def setup_from_config_path(self, path):
    env = get_env(self, path)
    set_things(self, env)


jaci_config_path = os.getenv('JACI_CONFIG_PATH') or '/etc/jaci.cfg'
setup_from_config_path(self, jaci_config_path)
