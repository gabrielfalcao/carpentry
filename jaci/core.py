#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import logging
from tumbler.core import Web
from flask.ext.github import GitHub


class JaciHttpServer(Web):
    LOGHANDLERS = ['lineup.steps', 'lineup', 'tumbler', 'jaci']

    def __init__(self, log_level=logging.INFO, *args, **kw):
        super(JaciHttpServer, self).__init__(*args, **kw)
        self.flask_app.config.from_object('jaci.conf')
        self.github = GitHub(self.flask_app)
        self.setup_logging(log_level)

    def setup_logging(self, level):
        logging.getLogger('cqlengine.cql').setLevel(logging.WARNING)
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

        for name in self.LOGHANDLERS:
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)
