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
    level=logging.INFO,
)

root_node = Node(__file__).dir

application = Web(
    template_folder=root_node.join('templates'),
    static_folder=root_node.join('jaci/static'),
    static_url_path='/assets',
    use_sqlalchemy=False
)
