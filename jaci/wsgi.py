#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# flake8: noqa
import os
import logging
from plant import Node
from jaci import routes

from jaci.core import JaciHttpServer

log_path = os.getenv('JACI_LOG_PATH', '/var/log/jaci.log')

logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
)

root_node = Node(__file__).dir

application = JaciHttpServer(
    log_level=logging.INFO,
    template_folder=root_node.join('templates'),
    static_folder=root_node.join('static'),
    static_url_path='/static',
    use_sqlalchemy=False
)
