#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time
import pika
from threading import Thread


def get_channel(connection):
    channel = connection.channel()
    channel.exchange_declare(exchange='test_exchange', exchange_type='topic')
    channel.queue_declare(queue='test_queue')
    channel.queue_unbind(queue='test_queue', exchange='test_exchange', routing_key='test_routing_key')
    return channel


def on_message(channel, method_frame, header_frame, body):
    print method_frame.delivery_tag
    print body
    print
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)


def consume():
    connection = pika.BlockingConnection()
    channel = get_channel(connection)
    channel.basic_consume(on_message, 'test_queue')
    channel.start_consuming()
# channel.stop_consuming()
# connection.close()


consumption = Thread(target=consume)
consumption.start()

connection = pika.BlockingConnection()
channel = get_channel(connection)

for x in range(10):

    channel.basic_publish('test_exchange',
                          'test_routing_key',
                          'message body value',
                          pika.BasicProperties(content_type='text/plain',
                                               delivery_mode=1))
    time.sleep(0.1)
