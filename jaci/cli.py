#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from __future__ import unicode_literals

import sys
import time
import json
import logging
import argparse
import warnings
import coloredlogs
from cqlengine import connection
from cqlengine.management import sync_table, drop_table, create_keyspace

from plant import Node
from lineup import JSONRedisBackend
from jaci.version import version
from jaci import routes
from jaci import conf
from jaci.core import JaciHttpServer, setup_logging
from jaci.api.v1 import get_models
from jaci.workers.pipelines import LocalBuilder

this_node = Node(__file__).dir


LOGO = '''\033[1;32m
     gg                         gg
     ""                         ""
     gg    ,gggg,gg    ,gggg,   gg
     8I   dP"  "Y8I   dP"  "Yb  88
    ,8I  i8`    ,8I  i8`        88
  _,d8I ,d8,   ,d8b,,d8,_    __,88,_
888P"888P"Y8888P"`Y8P""Y8888PP8P""Y8
   ,d8I`
 ,dP`8I  \033[1;35mContinuous Integration\033[1;32m
,8"  8I  \033[1;35mfor the \033[1;32mpeople\033[1;32m
I8   8I
`8, ,8I
 `Y8P"\033[0m
'''


def args_include_debug_or_info():
    return len(sys.argv) > 1 and sys.argv[1] in ['--debug', '--info']


def get_remaining_sys_argv():
    if args_include_debug_or_info():
        argv = sys.argv[3:]
    else:
        argv = sys.argv[2:]

    return argv


def jaci_version():
    parser = argparse.ArgumentParser(
        prog='jaci version --json',
        description='prints the software version')

    parser.add_argument('--json', action='store_true', default=False, help='shows the version as a json')

    args = parser.parse_args(get_remaining_sys_argv())

    if args.json:
        print json.dumps({'version': version, 'name': 'Jaci'}, indent=2)
    else:
        print LOGO
        print 'version {0}'.format(version)


def jaci_run():
    parser = argparse.ArgumentParser(
        prog='jaci run',
        description='runs jaci in the given port, defaults to 5000')

    parser.add_argument('-p', '--port', action='store_true', default=5000, help='the http port where jaci will listen')
    parser.add_argument('--host', default='localhost', help='the hostname to listen to')

    args = parser.parse_args(get_remaining_sys_argv())
    server = JaciHttpServer(
        log_level=logging.DEBUG,
        template_folder=this_node.join('templates'),
        static_folder=this_node.join('static'),
        static_url_path='/assets',
        use_sqlalchemy=False,
    )
    coloredlogs.install(logging.DEBUG)

    print LOGO
    print "listening on http://{0}:{1}".format(args.host, args.port)
    server.run(port=args.port, host=args.host)


class Spinner(object):
    steps = [
        r'|',
        r'/',
        r'-',
        '\\',

    ]

    def __init__(self, stream=None):
        self.state = 0
        self.stream = stream or sys.stdout

    def next(self):
        if self.state != 0:
            position = self.state % 4
            base = "\033[A\rwaiting for work {0}\n"
        else:
            position = 0
            base = "\rwaiting for work {0}\n"

        symbol = self.steps[position]
        self.stream.write(base.format(symbol))
        self.state += 1


def jaci_run_local_pipeline():
    parser = argparse.ArgumentParser(
        prog='jaci local-workers',
        description='waiting for jobs')

    parser.parse_args(get_remaining_sys_argv())

    print LOGO
    pipeline = LocalBuilder(JSONRedisBackend)

    coloredlogs.install(level=logging.INFO)
    setup_logging(logging.INFO)

    pipeline.run_daemon()
    try:
        while pipeline.started:
            time.sleep(0.1)

    except KeyboardInterrupt:
        pipeline.stop()


def jaci_setup():
    parser = argparse.ArgumentParser(
        prog='jaci setup',
        description='sets up the cassandra database')
    parser.add_argument('--drop', action='store_true', default=False, help='drop any existing tables before syncing')
    parser.add_argument('--flush-redis', action='store_true', default=False, help='flush all jaci-related redis keys')
    setup_logging(logging.INFO)
    args = parser.parse_args(get_remaining_sys_argv())
    coloredlogs.install(logging.INFO)

    print LOGO
    connection.setup(conf.cassandra_hosts, default_keyspace='jaci')

    create_keyspace('jaci', strategy_class='SimpleStrategy', replication_factor=3, durable_writes=True)
    pipeline = LocalBuilder(JSONRedisBackend)
    backend = pipeline.get_backend()
    if args.flush_redis:
        for key in backend.redis.keys('jaci*'):
            logging.warning("redis: deleting key %s", key)
            backend.redis.delete(key)

    for t in get_models():
        try:
            if args.drop:
                logging.warning("cassandra: dropping table %s", t)
                drop_table(t)

            logging.info("cassandra: creating table %s", t)
            sync_table(t)
        except Exception:
            logging.exception('Failed to drop/sync %s', t)


def main():
    HANDLERS = {
        'version': jaci_version,
        'run': jaci_run,
        'setup': jaci_setup,
        'workers': jaci_run_local_pipeline,
    }

    parser = argparse.ArgumentParser(prog='jaci')

    parser.add_argument('command', help='Available commands:\n\n{0}\n'.format("|".join(HANDLERS.keys())))
    parser.add_argument('--debug', help='debug mode, prints debug logs to stderr', action='store_true', default=False)
    parser.add_argument('--info', help='info mode, prints info logs to stderr', action='store_true', default=False)

    if args_include_debug_or_info():
        argv = sys.argv[1:3]
    else:
        argv = sys.argv[1:2]

    args = parser.parse_args(argv)


    if args.command not in HANDLERS:
        parser.print_help()
        raise SystemExit(1)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            HANDLERS[args.command]()
        except Exception:
            logging.exception("Failed to execute %s", args.command)
            raise SystemExit(1)


if __name__ == '__main__':
    routes
    main()
