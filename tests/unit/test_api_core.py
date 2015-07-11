#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
from carpentry.api.core import TokenAuthority


def test_authenticator_get_token():
    ('TokenAuthority.get_token() should parse the '
     'token from the given Authorization header')
