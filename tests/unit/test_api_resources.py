#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import os
import uuid
from os.path import join, abspath, dirname
from mock import patch, Mock, call
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
from carpentry.api.resources import create_build
from carpentry.api.resources import create_builder
from carpentry.api.resources import set_preferences
from carpentry.api.resources import edit_builder
from carpentry.api.resources import remove_builder
from carpentry.api.resources import list_builders
from carpentry.api.resources import builds_from_builder
from carpentry.api.resources import clear_builds
from carpentry.api.resources import retrieve_builder
from carpentry.api.resources import get_build
from carpentry.api.resources import get_conf
from carpentry.api.resources import get_user
from carpentry.api.resources import generate_ssh_key_pair
from carpentry.api.resources import trigger_builder_hook
from carpentry.api.resources import list_images
from carpentry.api.resources import list_containers
from carpentry.api.resources import stop_container
from carpentry.api.resources import remove_container
from carpentry.api.resources import remove_image
from carpentry.api.resources import get_github_repos


local_file = lambda *path: abspath(join(dirname(__file__), *path))
PROJECT_FILE = lambda *path: abspath(local_file('..', '..', *path))

test_uuid = uuid.UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3')


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
    ('POST /api/builder should generate ssh keys')
    user = TokenAuthority.return_value.get_user.return_value
    user.github_access_token = 'lemmeingithub'
    builder = models.Builder.create.return_value
    builder.to_dict.return_value = {'foo': 'bar'}

    generate_ssh_key_pair.return_value = ('privte', 'public')
    ensure_json_request.return_value = {
        'name': 'my-project',
        'git_uri': 'git@github.com:cnry/my-project.git',
        'shell_script': 'make',
        'json_instructions': '{}',
        'generate_ssh_keys': True,
    }

    # when i call create_builder
    response = create_builder()

    # then the response should be json
    response.should.equal(json_response.return_value)

    builder.cleanup_github_hooks.assert_called_once_with()
    builder.set_github_hook.assert_called_once_with(
        'lemmeingithub'
    )

    json_response.assert_called_once_with(
        {
            'foo': 'bar'
        },
        status=200
    )


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_retrieve_builder(json_response, models, TokenAuthority, request):
    ('GET /api/builder/<id> should return a a builder')

    # Given that Build.objects.get returns a mocked build
    builder = models.Builder.objects.get.return_value
    builder.to_dict.return_value = {'say': 'whaaaaat'}

    # When I call retrieve_builder
    response = retrieve_builder(id='someid')

    # Then the response should be json
    response.should.equal(json_response.return_value)
    models.Builder.objects.get.assert_called_once_with(
        id='someid')

    json_response.assert_called_once_with({'say': 'whaaaaat'})


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_clear_builds(json_response, models, TokenAuthority, request):
    ('DELETE /api/builder/:id/builds should delete all the '
     'builds that are linked to the given builder')

    class Build:
        def __init__(self, x):
            self.commit = str(x)[0] * 4

    # Given that Build.objects.get returns a mocked build
    builder = models.Builder.get.return_value
    builder.clear_builds.return_value = [
        Build(x) for x in range(10)]

    # When I call clear_builds
    response = clear_builds(id='someid')

    # Then delete() was called
    builder.clear_builds.assert_called_once_with()

    # And the query was done appropriately
    models.Builder.get.assert_called_once_with(
        id='someid'
    )

    # And the response should be a json_response
    response.should.equal(json_response.return_value)

    # And the json response was called appropriately
    json_response.assert_called_once_with(
        {'total': 10}
    )


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_clear_builds_empty(json_response, models, TokenAuthority, request):
    ('DELETE /api/builder/:id/builds should return '
     '0 when')

    # Given that Build.objects.get returns a mocked build
    builder = models.Builder.get.return_value
    builder.clear_builds.return_value = []

    # When I call clear_builds
    response = clear_builds(id='someid')

    # Then delete() was called
    builder.clear_builds.assert_called_once_with()

    # And the query was done appropriately
    models.Builder.get.assert_called_once_with(
        id='someid'
    )

    # And the response should be a json_response
    response.should.equal(json_response.return_value)

    # And the json response was called appropriately
    json_response.assert_called_once_with(
        {'total': 0}
    )


@patch('carpentry.api.core.ensure_json_request')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_edit_builder(json_response, models, TokenAuthority, request, ensure_json_request):
    ('PUT /api/builder/<id> should edit the builder')

    ensure_json_request.return_value = {
        'name': 'my-project',
        'git_uri': 'git@github.com:cnry/my-project.git',
        'shell_script': 'make',
        'json_instructions': None,
    }

    # Given that Build.objects.put returns a mocked build
    builder = models.Builder.objects.get.return_value
    builder.to_dict.return_value = {'say': 'whaaaaat'}

    # When I call retrieve_builder
    response = edit_builder(id='someid')

    # Then the response should be json
    response.should.equal(json_response.return_value)
    models.Builder.objects.get.assert_called_once_with(
        id='someid')

    json_response.assert_called_once_with({'say': 'whaaaaat'})


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_list_builders(json_response, models, TokenAuthority, request):
    ('GET /api/builder/<id> should list the builders')

    builder1 = Mock(name='builder1')
    builder1.to_dict.return_value = {'build': 1}
    builder2 = Mock(name='builder2')
    builder2.to_dict.return_value = {'build': 2}

    # Given that Build.objects.put returns a mocked build
    models.Builder.objects.all.return_value = [
        builder1,
        builder2,
    ]

    # When I call retrieve_builder
    response = list_builders()

    # Then the response should be json
    response.should.equal(json_response.return_value)
    json_response.assert_called_once_with([
        {
            'build': 1
        },
        {
            'build': 2
        }
    ])


@patch('carpentry.api.resources.ensure_json_request')
@patch('carpentry.api.resources.uuid')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_set_preferences(json_response, models, TokenAuthority, request, uuid_mock, ensure_json_request):
    ('POST /api/preferences should set the values')
    ensure_json_request.return_value = {
        'global_id_rsa_private_key': 'private',
        'global_id_rsa_public_key': 'public',
        'docker_registry_url': None,
    }
    uuid_mock.uuid1.return_value = test_uuid

    # When I call set_preferences
    response = set_preferences()

    # Then the response should be json
    response.should.equal(json_response.return_value)
    models.CarpentryPreference.create.assert_has_calls([
        call(value=u'public', id=test_uuid, key=u'global_id_rsa_public_key'),
        call(value=u'private', id=test_uuid, key=u'global_id_rsa_private_key')
    ])
    json_response.assert_called_once_with({
        'global_id_rsa_public_key': 'public',
        'global_id_rsa_private_key': 'private'
    })


@patch('carpentry.api.resources.ensure_json_request')
@patch('carpentry.api.resources.uuid')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_get_conf(json_response, models, TokenAuthority, request, uuid_mock, ensure_json_request):
    ('POST /api/preferences should set the values')
    ensure_json_request.return_value = {
        'global_id_rsa_private_key': 'private',
        'global_id_rsa_public_key': 'public',
        'docker_registry_url': None,
    }
    uuid_mock.uuid1.return_value = test_uuid

    # When I call get_conf
    response = get_conf()

    # Then the response should be json
    response.should.equal(json_response.return_value)
    json_response.call_args[0][0].should.equal({
        'default_subprocess_timeout_in_seconds': 1500,
        'DEFAULT_WORKDIR': '/tmp/carpentry',
        'carpentry_config_path': PROJECT_FILE('tests/carpentry.yml'),
        'workdir': 'sandbox',
        'SUPPORTED_CONFIG_PATHS': [
            '/etc/carpentry.yml',
            os.path.expanduser('~/carpentry.yml'),
            os.path.expanduser('~/.carpentry.yml'),
            PROJECT_FILE('carpentry.yml'),
        ],
        'full_server_url': 'http://localhost:5000',
        'ssh_executable_path': '/usr/bin/ssh',
        'config_path': PROJECT_FILE('carpentry.yml'),
        'redis_host': 'localhost',
        'hostname': 'localhost',
        'cassandra_hosts': ['127.0.0.1', '0.0.0.0'],
        'allowed_github_organizations': ['cnry'],
        'GITHUB_CLIENT_SECRET': 'ec27a8f0e4a436c3cd6c846c377ef18e4bc4b0de',
        'redis_db': 0,
        'git_executable_path': '/usr/bin/git',
        'redis_port': 6379,
        'SECRET_KEY': None,
        'fallback_config_path': '/etc/carpentry.yml',
        'port': 5000,
        'GITHUB_CLIENT_ID': 'd4d5fd91b48e183de039',
    })


@patch('carpentry.api.resources.uuid')
@patch('carpentry.api.resources.generate_ssh_key_pair')
@patch('carpentry.api.resources.ensure_json_request')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_create_build_generating_ssh_keys(json_response, models, TokenAuthority, request, ensure_json_request, generate_ssh_key_pair, uuid_mock):
    ('POST /api/build should generate ssh keys')
    user = TokenAuthority.return_value.get_user.return_value
    user.github_access_token = 'lemmeingithub'
    builder = models.Builder.objects.get.return_value
    builder.branch = 'master'

    generate_ssh_key_pair.return_value = ('privte', 'public')
    ensure_json_request.return_value = {
        'author_name': 'foo',
        'author_email': 'bar',
    }

    # when i call create_build
    response = create_build(id='builder-id')

    # then the response should be json
    response.should.equal(json_response.return_value)

    models.Builder.objects.get.assert_called_once_with(id='builder-id')
    builder.trigger.assert_called_once_with(
        user,
        branch=builder.branch,
        author_name='foo',
        author_email='bar',
    )


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_get_user(json_response, models, TokenAuthority, request):
    ('POST /api/build should generate ssh keys')
    user = TokenAuthority.return_value.get_user.return_value
    user.get_github_metadata.return_value = {
        'le': 'user'
    }

    # When i call create_build
    response = get_user()

    # then the response should be json
    response.should.equal(json_response.return_value)
    json_response.assert_called_once_with({
        'le': 'user'
    }, status=200)


@patch('carpentry.api.resources.uuid')
@patch('carpentry.api.resources.generate_ssh_key_pair')
@patch('carpentry.api.resources.ensure_json_request')
@patch('carpentry.api.resources.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_trigger_builder_hook(json_response, models, TokenAuthority, request, ensure_json_request, generate_ssh_key_pair, uuid_mock):
    ('POST /api/build should generate ssh keys')
    request.get_json.return_value = {
        'head_commit': {
            'id': 'thecommithash',
            'commiter': {
                'author_name': 'The Name',
                'author_email': 'the@name.com',
            }
        }
    }
    request.data = {'say': 'what'}
    user = models.User.get.return_value
    user.email = 'email@foo.com'
    user.name = 'Mary Doe'
    user.github_access_token = 'lemmeingithub'
    builder = models.Builder.objects.get.return_value
    builder.branch = 'master'

    generate_ssh_key_pair.return_value = ('privte', 'public')
    ensure_json_request.return_value = {
        'author_name': 'foo',
        'author_email': 'bar',
    }

    # when i call trigger_builder_hook
    response = trigger_builder_hook(id='builder-id')

    # then the response should be json
    response.should.equal(json_response.return_value)

    models.Builder.objects.get.assert_called_once_with(id='builder-id')
    builder.trigger.assert_called_once_with(
        user,
        author_email=u'email@foo.com',
        commit=u'thecommithash',
        github_webhook_data={u'say': u'what'},
        author_name=u'Mary Doe',
        branch='master',
    )


@patch('carpentry.api.resources.uuid')
@patch('carpentry.api.resources.generate_ssh_key_pair')
@patch('carpentry.api.resources.ensure_json_request')
@patch('carpentry.api.resources.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_trigger_builder_hook_missing_builder(json_response, models, TokenAuthority, request, ensure_json_request, generate_ssh_key_pair, uuid_mock):
    ('POST /api/build should generate ssh keys')
    request.get_json.return_value = {
        'head_commit': {
            'id': 'thecommithash',
            'commiter': {
                'author_name': 'The Name',
                'author_email': 'the@name.com',
            }
        }
    }
    request.data = {'say': 'what'}
    user = models.User.get.return_value
    user.email = 'email@foo.com'
    user.name = 'Mary Doe'
    user.github_access_token = 'lemmeingithub'
    models.Builder.objects.get.side_effect = Exception('boom')

    response = trigger_builder_hook(id='builder-id')

    # then the response should be json
    response.should.equal(json_response.return_value)

    models.Builder.objects.get.assert_called_once_with(
        id='builder-id'
    )
    json_response.assert_called_once_with({}, status=404)


@patch('carpentry.api.resources.get_docker_client')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_list_images(json_response, models, TokenAuthority, request, get_docker_client):
    ('GET /api/docker/images should return a sorted list of images')
    docker = get_docker_client.return_value
    docker.images.return_value = [
        {'Id': '4'},
        {'Id': '1'},
        {'Id': '2'},
    ]
    response = list_images()

    # then the response should be json
    response.should.equal(json_response.return_value)

    json_response.assert_called_once_with([
        {'Id': '1'},
        {'Id': '2'},
        {'Id': '4'},
    ])


@patch('carpentry.api.resources.get_docker_client')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_list_containers(json_response, models, TokenAuthority, request, get_docker_client):
    ('GET /api/docker/containers should return a sorted list of containers')
    docker = get_docker_client.return_value
    docker.containers.return_value = [
        {'Id': '4'},
        {'Id': '1'},
        {'Id': '2'},
    ]
    response = list_containers()

    # then the response should be json
    response.should.equal(json_response.return_value)

    json_response.assert_called_once_with([
        {'Id': '1'},
        {'Id': '2'},
        {'Id': '4'},
    ])


@patch('carpentry.api.resources.get_docker_client')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_stop_container(json_response, models, TokenAuthority, request, get_docker_client):
    ('POST /api/docker/container/:id/stop should stop the given container')
    docker = get_docker_client.return_value
    docker.stop.return_value = {'stopped': 'ok'}

    response = stop_container(container_id='thecontainerid')

    # then the response should be json
    response.should.equal(json_response.return_value)

    json_response.assert_called_once_with({
        'stopped': 'ok'
    })

    docker.stop.assert_called_once_with('thecontainerid', 5)


@patch('carpentry.api.resources.get_docker_client')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_remove_container(json_response, models, TokenAuthority, request, get_docker_client):
    ('POST /api/docker/container/:id/remove should remove the given container')
    docker = get_docker_client.return_value
    docker.remove_container.return_value = {'removed': 'ok'}

    response = remove_container(container_id='thecontainerid')

    # then the response should be json
    response.should.equal(json_response.return_value)

    json_response.assert_called_once_with({
        'removed': 'ok'
    })

    docker.remove_container.assert_called_once_with('thecontainerid', v=True)


@patch('carpentry.api.resources.get_docker_client')
@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_remove_image(json_response, models, TokenAuthority, request, get_docker_client):
    ('POST /api/docker/image/:id/remove should remove the given image')
    docker = get_docker_client.return_value
    docker.remove_image.return_value = {'removed': 'ok'}

    response = remove_image(image_id='theimageid')

    # then the response should be json
    response.should.equal(json_response.return_value)

    json_response.assert_called_once_with({
        'removed': 'ok'
    })

    docker.remove_image.assert_called_once_with(
        'theimageid',
        noprune=False,
        force=True
    )


@patch('carpentry.api.core.request')
@patch('carpentry.api.core.TokenAuthority')
@patch('carpentry.api.resources.models')
@patch('carpentry.api.resources.json_response')
def test_get_github_repos(json_response, models, TokenAuthority, request):
    ('POST /api/build should generate ssh keys')
    user = TokenAuthority.return_value.get_user.return_value
    user.retrieve_and_cache_github_repositories.return_value = {
        'le': 'repositories'
    }

    # When i call create_build
    response = get_github_repos()

    # then the response should be json
    response.should.equal(json_response.return_value)
    json_response.assert_called_once_with({
        'le': 'repositories'
    })
