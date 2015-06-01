#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import gevent
import gevent.monkey
gevent.monkey.patch_all()
from gevent.event import AsyncResult

import logging
from haigha.connection import Connection
from haigha.message import Message


def close(ch):
    conn.close()

conn = Connection(
    transport='gevent',
    close_cb=close,
    logger=logging.getLogger())

waiter = AsyncResult()


def message_pump():
    print "Entering Message Pump"
    try:
        while conn is not None:
            # Pump
            conn.read_frames()

            # Yield to other greenlets so they don't starve
            gevent.sleep(0.1)
    finally:
        print "Leaving Message Pump"
        waiter.set()


gevent.spawn(message_pump)


def handle_message_received(msg):
    print "received message: %s" % (msg, )


channel = conn.channel()
# todo: try to rename jacipub with jaci.pub
channel.exchange.declare('jacipub', 'topic')
channel.queue.declare('jaci.builds')
channel.queue.bind('jaci.builds', 'jacipub', routing_key='jaci.builds.*')


def send_message(body):
    msg = Message(body, application_headers={'foo': 'bar'})
    print "Publising message: %s" % (msg,)
    try:
        channel.basic.publish(msg, 'test_exchange', 'test_routing_key')
    except Exception as e:
        print e

messages = ['foo', 'bar']
gevent.sleep(0)

while True:
    try:
        gevent.sleep(.1)
        if messages:
            send_message(messages.pop())

    except KeyboardInterrupt:
        print "BYE"
        break
