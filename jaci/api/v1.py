#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals

import json
import base64
import logging
from dateutil.parser import parse as parse_datetime
from tumbler import tumbler
from tumbler import json_response

web = tumbler.module(__name__)

# from jaci.models import Post
from jaci.api.core import authenticated, ensure_json_request
from jaci.models import User, NewsletterSubscription, Post


def autodatetime(s):
    return s and parse_datetime(s) or None


@web.post('/api/posts')
@authenticated
def create_post(user):
    data = ensure_json_request({
        'title': unicode,
        'slug': any,
        'body': any,
        'description': any,
        'link': any,
        'date_published': autodatetime,
    })

    post = user.create_post(**data)
    logging.info('creating post %s by %s', post.title, user.email)

    return json_response(post.to_dict())


@web.put('/api/posts/<uuid>')
@authenticated
def edit_post(user, uuid):
    data = ensure_json_request({
        'title': any,
        'slug': any,
        'body': any,
        'date_published': autodatetime,
        'description': any,
        'link': any,
    })

    post = user.edit_post(uuid, data)
    logging.info('editing post %s by %s', post.title, user.email)

    return json_response(post.to_dict())


@web.get('/api/posts/<uuid>')
@authenticated
def retrieve_post(user, uuid):
    post = user.get_post(uuid)
    logging.info('editing post %s by %s', post.title, user.email)

    return json_response(post.to_dict())


@web.delete('/api/posts/<uuid>')
@authenticated
def delete_post(user, uuid):
    deleted = user.delete_post(uuid)
    if deleted:
        status = 'OK'
    else:
        status = 'error'

    logging.info('deleting post %s by %s: %s', uuid, user.email, status)

    if not deleted:
        return json_response({'result': 'error'}, 500)

    return json_response(deleted.to_dict())


def parse_auth_payload():
    data = ensure_json_request({
        'info': unicode,
    })
    info = data['info']
    raw = base64.b64decode(info)
    return json.loads(raw)


@web.post('/api/auth')
def authenticate_user():
    data = parse_auth_payload()

    email = data.pop('email')
    given_password = data.pop('password')

    token = User.authenticate(email, given_password)
    if token:
        return json_response({
            'token': token.token,
            'created_at': token.date_created.isoformat()
        })

    return json_response({
        'result': 'error',
        'message': 'could not authenticate'
    }, 401)


@web.post('/api/newsletter/subscribe')
def subscribe_newsletter():
    data = ensure_json_request({
        'email': unicode,
        'name': any
    })

    email = data.pop('email')
    name = data.pop('name', None)

    subscription = NewsletterSubscription.subscribe(name, email)

    if not subscription:
        return json_response({
            'result': 'error',
            'message': 'could not create subscription',
            'meta': {'email': email, 'name': name}
        }, 400)

    return json_response({
        'result': 'OK',
        'message': 'newsletter subscription created',
        'id': subscription.id
    })


@web.get('/api/posts/latest')
def latest_posts():
    posts = Post.objects.all()
    results = [p.to_dict() for p in posts]
    return json_response(results)
