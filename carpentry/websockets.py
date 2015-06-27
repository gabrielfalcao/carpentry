#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from flask_socketio import emit

from carpentry.registry import websocket_handler as websocket_when


@websocket_when('build')
def test_message(message):
    emit('my response', {'data': 'got it!'})
