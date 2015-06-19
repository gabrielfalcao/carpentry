#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import re
import logging

from tumbler import tumbler
from flask import request, abort
web = tumbler.module(__name__)

from functools import wraps
from jaci.models import User


class Authenticator(object):
    regex = re.compile(r'Bearer:?\s+([\w-]{36})\s*')

    def __init__(self, headers):
        self.bearer = headers.get('Authorization')

    def parse_bearer_string(self, bearer):
        found = self.regex.search(bearer)
        if found:
            return found.group(1)

    def get_token_string(self):
        if not self.bearer:
            logging.info("Missing `Authorization` header %s", request.headers)
            abort(400)
        return self.parse_bearer_string(self.bearer)

    def get_token(self):
        string = self.get_token_string()
        return string

    def get_user(self):

        token = self.get_token()
        user = User(
            name=token,
            token=token,
            email='{0}@jaci.io'.format(token)
        )
        return user


def authenticated(resource):
    @wraps(resource)
    def decorator(*args, **kw):
        auth = Authenticator(request.headers)
        kw['user'] = auth.get_user()
        return resource(*args, **kw)

    return decorator


def ensure_json_request(spec, fallback={}):
    data = request.get_json(silent=True) or fallback
    if not data:
        logging.error('missing json body')
        abort(400)

    result = {}
    for key, validator in spec.items():
        value = data.get(key)
        if validator is any:
            result[key] = value
            continue

        try:
            result[key] = validator(value)
        except:
            logging.exception('Could not validate %s from %s', key, data)
            abort(400)

    return result
