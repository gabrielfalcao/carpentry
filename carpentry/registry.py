# -*- coding: utf-8 -*-
#
from collections import OrderedDict

WEBSOCKET_HANDLERS = OrderedDict()


def websocket_handler(event_name):
    def decorator(func):
        WEBSOCKET_HANDLERS[event_name] = func
        return func

    return decorator
