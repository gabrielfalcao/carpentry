#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# flake8: noqa
import os
import logging
from plant import Node
from jaci import routes

from tumbler.core import Web

log_path = os.getenv('TIMELESS_LOG_PATH', '/var/log/jaci.log')

logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
)

root_node = Node(__file__).dir

application = Web()


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    make_server('', 8000, application).serve_forever()
