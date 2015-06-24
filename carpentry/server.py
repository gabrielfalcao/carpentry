#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals


def get_absolute_url(path):
    return 'http://localhost:5000/{0}'.format(path.lstrip('/'))
