#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
from mock import patch, Mock
from carpentry.models import (
    Build,
    Builder,
    CarpentryPreference,
    GithubOrganization,
    GithubRepository,
    User,
)
from carpentry.models import CarpentryBaseModel

from carpentry.api.resources import is_model
from carpentry.api.resources import get_models
from carpentry.api.resources import remove_build
from carpentry.api.resources import create_builder
from carpentry.api.resources import edit_builder
from carpentry.api.resources import remove_builder
from carpentry.api.resources import list_builders
from carpentry.api.resources import builds_from_builder
from carpentry.api.resources import clear_builds
from carpentry.api.resources import retrieve_builder
from carpentry.api.resources import get_build
from carpentry.api.resources import generate_ssh_key_pair


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_remove_build(json_response, models, TokenAuthority, request):
    ('DELETE /api/build/<id> should retrieve a build by '
     'id and delete it')

    # Given that Build.objects.get returns a mocked build
    build = models.Build.objects.get.return_value

    # When I call remove_build
    response = remove_build(id='someid')

    # Then delete() was called
    build.delete.assert_called_once_with()

    # And the query was done appropriately
    models.Build.objects.get.assert_called_once_with(
        id='someid'
    )

    # And the response should be a json_response
    response.should.equal(json_response.return_value)

    # And the json response was called appropriately
    json_response.assert_called_once_with(
        build.to_dict.return_value,
    )


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_remove_builder(json_response, models, TokenAuthority, request):
    ('DELETE /api/builder/<id> should retrieve a builder by '
     'id and delete it')

    # Given that Builder.objects.get returns a mocked builder
    builder = models.Builder.objects.get.return_value

    # When I call remove_builder
    response = remove_builder(id='someid')

    # Then delete() was called
    builder.delete.assert_called_once_with()

    # And the query was done appropriately
    models.Builder.objects.get.assert_called_once_with(
        id='someid'
    )

    # And the response should be a json_response
    response.should.equal(json_response.return_value)

    # And the json response was called appropriately
    json_response.assert_called_once_with(
        builder.to_dict.return_value
    )


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_builds_from_builder(json_response, models, TokenAuthority, request):
    ('GET /api/builder/<id>/builds should retrieve list of builds')

    build1 = Mock(name='build1')
    build1.to_dict.return_value = {'build': 1}

    build2 = Mock(name='build2')
    build2.to_dict.return_value = {'build': 2}

    models.Builds.objects.filter.return_value = [build1, build2]

    # When I call remove_builder
    response = builds_from_builder(id='someid')

    # Then the query was done appropriately
    models.Build.objects.filter.assert_called_once_with(
        builder_id='someid'
    )

    # And the response should be a json_response
    response.should.equal(json_response.return_value)


def test_is_model():
    ("is_model() returns True if it's a model")

    is_model(User).should.be.true
    is_model(object).should.be.false
    is_model(CarpentryBaseModel).should.be.false


def test_get_models():
    ('get_models() returns all the declared carpentry models')

    get_models().should.equal([
        Build,
        Builder,
        CarpentryPreference,
        GithubOrganization,
        GithubRepository,
        User,
    ])


@patch('carpentry.api.resources.RSA')
def test_generate_ssh_key_pair(RSA):
    ('generate_ssh_key_pair() should generate an '
     'RSA 2048 private key and retrieve its public key')

    # Given that RSA is mocked
    private_key = RSA.generate.return_value
    public_key = private_key.publickey.return_value
    private_key.exportKey.return_value = 'the-PEM'
    public_key.exportKey.return_value = 'the-pub'

    # When I cal generate_ssh_key_pair
    result = generate_ssh_key_pair()

    # Then it should return a tuple with 2 items
    result.should.equal(('the-PEM', 'the-pub'))


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_get_build_failed(json_response, models, TokenAuthority, request):
    ('GET /api/build/<id> should return a 404 if '
     'an exception happens')

    # Given that Build.objects.get returns a mocked build
    models.Build.get.side_effect = RuntimeError('boom')

    # When I call retrieve_build
    response = get_build(id='someid')

    # Then get() was called
    models.Build.get.assert_called_once_with(id='someid')

    # And the response should be a json_response
    response.should.equal(json_response.return_value)

    # And the json response was called appropriately
    json_response.assert_called_once_with(
        {'error': 'boom'}, status=404
    )


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_get_build_ok(json_response, models, TokenAuthority, request):
    ('GET /api/build/<id> should return a 404 if '
     'an exception happens')

    # Given that Build.objects.get returns a mocked build
    build = models.Build.get.return_value
    build.to_dict.return_value = {'build': 'me'}
    build.builder.to_dict.return_value = {'builder': 'too'}

    # When I call retrieve_build
    response = get_build(id='someid')

    # Then get() was called
    models.Build.get.assert_called_once_with(id='someid')

    # And the response should be a json_response
    response.should.equal(json_response.return_value)

    # And the json response was called appropriately
    json_response.assert_called_once_with(
        {u'builder': u'too', u'build': u'me'}
    )


@patch('carpentry.api.resources.uuid')
@patch('carpentry.api.resources.generate_ssh_key_pair')
@patch('carpentry.api.core.ensure_json_request')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_create_builder_generating_ssh_keys(json_response, models, TokenAuthority, request, ensure_json_request, generate_ssh_key_pair, uuid_mock):
    ('POST /api/builder should ')

    generate_ssh_key_pair.return_value = ('privte', 'public')
    ensure_json_request.return_value = {
        'name': 'my-project',
        'git_uri': 'git@github.com:cnry/my-project.git',
        'shell_script': 'make',
        'json_instructions': '{}',
        'id_rsa_private': 'private',
        'id_rsa_public': 'public',
        'generate_ssh_keys': 'keys',
    }

    # When I call create_builder
    response = create_builder()

    # Then the response should be json
    response.should.equal(json_response.return_value)
