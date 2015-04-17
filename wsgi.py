#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# flake8: noqa
import os
import logging
from plant import Node
from jaci import routes

from tumbler.core import Web

log_path = os.getenv('JACI_LOG_PATH', 'jaci.log')

logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
)

root_node = Node(__file__).dir

application = Web(use_sqlalchemy=False)


if __name__ == '__main__':
    from gevent.wsgi import WSGIServer
    http_server = WSGIServer(('', 8000), application)
    http_server.serve_forever()
