#!/usr/bin/env python
# -*- coding: utf-8 -*-
import httpretty

import uuid
import json
from sure import scenario

from tumbler.core import Web
from repocket import configure
from carpentry.api import resources
from carpentry.models import User


class GithubMocker(object):
    resources  # dummy line

    def __init__(self, user):
        self.user = user

    def on_post(self, path, body=None, status=200, headers=None):
        if headers is None:
            headers = {}
        httpretty.register_uri(
            httpretty.POST,
            "/".join(["https://api.github.com", path.lstrip('/')]),
            body=body,
            headers=headers,
            status=status
        )

    def on_get(self, path, body=None, status=200, headers=None):
        if headers is None:
            headers = {}
        url = "/".join(["https://api.github.com", path.lstrip('/')])
        httpretty.register_uri(
            httpretty.GET,
            url,
            body=body,
            headers=headers,
            status=status
        )

    def on_put(self, path, body=None, status=200, headers=None):
        if headers is None:
            headers = {}
        httpretty.register_uri(
            httpretty.PUT,
            "/".join(["https://api.github.com", path.lstrip('/')]),
            body=body,
            headers=headers,
            status=status
        )

    def on_delete(self, path, body=None, status=200, headers=None):
        if headers is None:
            headers = {}
        httpretty.register_uri(
            httpretty.DELETE,
            r"/".join([r"https://api.github.com", path.lstrip('/')]),
            body=body,
            headers=headers,
            status=status
        )


def prepare_redis(context):
    context.pool = configure.connection_pool(
        hostname='localhost',
        port=6379
    )
    context.connection = context.pool.get_connection()
    sweep_redis(context)


def sweep_redis(context):
    context.connection.flushall()


def prepare_http_client(context):
    context.web = Web()
    context.http = context.web.flask_app.test_client()
    context.user = User(
        carpentry_token=uuid.uuid4(),
        github_access_token='Default:FAKE:Token'
    )
    context.user.save()

    httpretty.enable()
    context.github = GithubMocker(context.user)
    context.github.on_get('/user/orgs', body=json.dumps(
        [
            {'login': 'cnry'},
        ]
    ))

    context.github.on_get('/user', body=json.dumps({
        "login": "octocat",
        "id": 1,
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "gravatar_id": "",
        "url": "https://api.github.com/users/octocat",
        "html_url": "https://github.com/octocat",
        "followers_url": "https://api.github.com/users/octocat/followers",
        "following_url": "https://api.github.com/users/octocat/following{/other_user}",
        "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
        "organizations_url": "https://api.github.com/users/octocat/orgs",
        "repos_url": "https://api.github.com/users/octocat/repos",
        "events_url": "https://api.github.com/users/octocat/events{/privacy}",
        "received_events_url": "https://api.github.com/users/octocat/received_events",
        "type": "User",
        "site_admin": False,
        "name": "monalisa octocat",
        "company": "GitHub",
        "blog": "https://github.com/blog",
        "location": "San Francisco",
        "email": "octocat@github.com",
        "hireable": False,
        "bio": "There once was...",
        "public_repos": 2,
        "public_gists": 1,
        "followers": 20,
        "following": 0,
        "created_at": "2008-01-14T04:33:35Z",
        "updated_at": "2008-01-14T04:33:35Z",
        "total_private_repos": 100,
        "owned_private_repos": 100,
        "private_gists": 81,
        "disk_usage": 10000,
        "collaborators": 8,
        "plan": {
            "name": "Medium",
            "space": 400,
            "private_repos": 20,
            "collaborators": 0
        }
    }))

    context.headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer: {0}'.format(context.user.carpentry_token)
    }


def disable_httpretty(context):
    httpretty.disable()

safe_db = scenario(prepare_redis, sweep_redis)
api = scenario([prepare_redis, prepare_http_client], [sweep_redis, disable_httpretty])
