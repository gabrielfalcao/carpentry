#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import json
import requests
from jaci.models import Build
from lineup import Step


class GitClone(Step):
    def after_consume(self, instructions):
        msg = "Done git cloning {git_uri}".format(**instructions)
        self.log(msg)

    def before_consume(self):
        self.log("ready to git clone")

    def consume(self, instructions):
        url = instructions['url']
        method = instructions.get('method', 'get').lower()

        http_request = getattr(requests, method)
        response = http_request(url)
        instructions['download'] = {
            'content': response.content,
            'headers': dict(response.headers),
            'status_code': response.status_code,
        }
        self.produce(instructions)
