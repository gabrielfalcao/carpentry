#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
from mock import patch
from carpentry.api.core import TokenAuthority, authenticated


def test_authenticator_get_token():
    ('TokenAuthority.get_token() should parse the '
     'token from the given Authorization header')

    # Given a headers dict with a valid token
    headers = {
        'Authorization': 'Bearer: thetoken'
    }

    # And an instance of TokenAuthority that uses it
    authority = TokenAuthority(headers)

    # When I call get_token()
    result = authority.get_token()

    # Then it should match the relevant token part of the header string
    result.should.equal('thetoken')


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.abort')
def test_get_token_string_missing_header(abort, request):
    ('TokenAuthority.get_token_string() should parse the '
     'token from the given Authorization header')

    # Given a headers dict with a valid token
    headers = {}

    # And an instance of TokenAuthority that uses it
    authority = TokenAuthority(headers)

    # When I call get_token_string()
    authority.get_token_string()

    # Then it should have aborted the request
    abort.assert_called_once_with(401)


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.abort')
def test_get_user_none(abort, request):
    ('TokenAuthority.get_user() should abort immediately if the token is None')

    # Given a headers dict with a valid token
    headers = {
        'Authorization': 'boo'
    }

    # And an instance of TokenAuthority that uses it
    authority = TokenAuthority(headers)

    # When I call get_user
    authority.get_user()

    # Then it should have aborted the request
    abort.assert_called_once_with(401)


@patch('carpentry.api.core.g')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.abort')
@patch('carpentry.api.core.User')
def test_get_user_bad_token(User, abort, request, g):
    ('TokenAuthority.get_user() should abort immediately if the token is None')

    # Given that no user can be found with the given token
    User.from_carpentry_token.return_value = None

    # Given a headers dict with a valid token
    headers = {
        'Authorization': 'Bearer: thetoken'
    }

    # And an instance of TokenAuthority that uses it
    authority = TokenAuthority(headers)

    # When I call get_user
    authority.get_user()

    # Then it should have aborted the request
    abort.assert_called_once_with(401)


@patch('carpentry.api.core.g')
@patch('carpentry.api.core.conf')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.abort')
@patch('carpentry.api.core.User')
def test_get_user_ok(User, abort, request, conf, g):
    ('TokenAuthority.get_user() should succeed if the user organization is in the allowed ones')
    conf.allowed_github_organizations = ['cnry']
    # Given that no user can be found with the given token
    user = User.from_carpentry_token.return_value
    user.organization_names = ['cnry']

    # Given a headers dict with a valid token
    headers = {
        'Authorization': 'Bearer: thetoken'
    }

    # And an instance of TokenAuthority that uses it
    authority = TokenAuthority(headers)

    # When I call get_user
    result = authority.get_user()

    # Then it should return the user
    result.should.equal(user)


@patch('carpentry.api.core.g')
@patch('carpentry.api.core.conf')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.abort')
@patch('carpentry.api.core.User')
def test_get_user_bad_organization(User, abort, request, conf, g):
    ('TokenAuthority.get_user() should abort with 401 if the user is from another organization')
    conf.allowed_github_organizations = ['cnry']

    # Given that no user can be found with the given token
    user = User.from_carpentry_token.return_value
    user.organization_names = ['dropcam']

    # Given a headers dict with a valid token
    headers = {
        'Authorization': 'Bearer: thetoken'
    }

    # And an instance of TokenAuthority that uses it
    authority = TokenAuthority(headers)

    # When I call get_user
    authority.get_user()

    # Then it should return the user
    abort.assert_called_once_with(401)


@patch('carpentry.api.core.json_response')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
def test_authenticated_ok(TokenAuthority, request, json_response):
    ('@authenticated should return the result of the original decorated function')

    TokenAuthority.return_value.get_user.return_value = 'na'

    # Given some valid request headers
    request.headers = {
        'Authorization': 'Bearer: thetoken'
    }

    # And a function decorated with @authenticated
    @authenticated
    def yay(user):
        return '-'.join([user] * 8) + ' batman'

    # When I call it
    result = yay()

    # Then it should have returned a json_response
    result.should.equal('na-na-na-na-na-na-na-na batman')


@patch('carpentry.api.core.request')
def test_ensure_json_request(request):
    ('@authenticated should return the result of the original decorated function')

    TokenAuthority.return_value.get_user.return_value = 'na'

    # Given some valid request headers
    request.headers = {
        'Authorization': 'Bearer: thetoken'
    }

    # And a function decorated with @authenticated
    @authenticated
    def yay(user):
        return '-'.join([user] * 8) + ' batman'

    # When I call it
    result = yay()

    # Then it should have returned a json_response
    result.should.equal('na-na-na-na-na-na-na-na batman')
