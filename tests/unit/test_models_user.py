#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
from mock import patch
from carpentry.models import User


def test_user_get_github_metadata_cached():
    ('User.get_github_metadata should return the cached '
     'data when available')

    # Given a user with a valid json meta
    u = User(github_metadata='{"foo": "bar"}')

    # When I call get_github_metadata
    result = u.get_github_metadata()

    # Then it should equal to the cached data
    result.should.equal({'foo': 'bar'})


@patch('carpentry.models.User.save')
@patch('carpentry.models.requests')
def test_user_get_github_metadata(requests, save):
    ('User.get_github_metadata should retrieve from api and save')

    response = requests.get.return_value
    response.text = '{"foo": "bar"}'
    response.json.return_value = {"foo": "bar"}

    # Given a user with a valid json meta
    u = User(
        github_access_token='test-token',
        carpentry_token=uuid.UUID(
            '4b1d90f0-96c2-40cd-9c21-35eee1f243d3')
    )

    # When I call get_github_metadata
    result = u.get_github_metadata()

    # Then it should equal to the cached data
    result.should.equal({'foo': 'bar'})

    save.assert_called_once_with()
