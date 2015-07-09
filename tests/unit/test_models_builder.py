#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
from mock import patch, Mock
from datetime import datetime, date, time

from carpentry.models import Builder


###########################
# Builder model tests

@patch('carpentry.models.User')
def test_builder_get_fallback_access_token(User):
    ('Builder.get_fallback_github_access_token returns the token from the user who created the builder')
    # Given that User is mocked to return an object with a valid string as github_access_token
    creator = User.get.return_value
    creator.github_access_token = 'free-pass-to-github-yay'

    # And a valid UUID
    user_uuid = uuid.UUID('a1ea566e-5608-4670-a215-60bc34311c65')

    # And an instance of builder with a valid user uuid
    instance1 = Builder(
        creator_user_id=user_uuid
    )

    # When I call get_fallback_github_access_token
    result = instance1.get_fallback_github_access_token()

    # And it should have returned
    result.should.equal('free-pass-to-github-yay')

    # And User.get should have been called with the creator_user_id as id
    User.get.assert_called_once_with(id=user_uuid)

    # And the property github_access_token returns the same
    instance1.github_access_token.should.equal(
        'free-pass-to-github-yay'
    )


@patch('carpentry.models.requests')
def test_builder_delete_single_github_hook(requests):
    ('Builder.delete_single_github_hook returns the token '
     'from the user who created the builder')

    # Given an instance of builder with a valid github uri
    builder = Builder(
        git_uri='git@github.com:owner/project.git'
    )

    # When I call delete_single_github_hook
    result = builder.delete_single_github_hook(
        'hook-id',
        'fake-token'
    )

    # Then requests.delete should have been called with the right url
    requests.delete.assert_called_once_with(
        'https://api.github.com/repos/owner/project/hooks/hook-id',
        headers={
            'Authorization': 'token fake-token'
        }
    )

    # And it should have returned the response
    result.should.equal(requests.delete.return_value)


@patch('carpentry.models.requests')
def test_builder_list_github_hooks_ok(requests):
    ('Builder.list_github_hooks returns the json response')

    response = requests.get.return_value
    response.json.return_value = [
        {
            'id': 11,
            'config': {
                'url': 'http://boohoo.io'
            }
        },
        {
            'id': 22,
            'config': {
                'url': 'http://chucknorr.is'
            }
        },
    ]

    # Given an instance of builder with a valid github uri
    builder = Builder(
        git_uri='git@github.com:owner/project.git'
    )

    # When I call list_github_hooks
    result = builder.list_github_hooks('fake-token')

    # Then requests.delete should have been called with the right url
    requests.get.assert_called_once_with(
        'https://api.github.com/repos/owner/project/hooks',
        headers={
            'Authorization': 'token fake-token'
        }
    )

    # And it should have returned the response
    result.should.equal([
        {
            'config': {
                'url': 'http://boohoo.io'
            },
            'id': 11
        },
        {
            'config': {
                'url': 'http://chucknorr.is'
            },
            'id': 22
        }
    ])


@patch('carpentry.models.requests')
def test_builder_list_github_hooks_failed(requests):
    ('Builder.list_github_hooks returns an empty list when failed')

    response = requests.get.return_value
    response.json.side_effect = ValueError('foo')

    # Given an instance of builder with a valid github uri
    builder = Builder(
        git_uri='git@github.com:owner/project.git'
    )

    # When I call list_github_hooks
    result = builder.list_github_hooks('fake-token')

    # Then requests.delete should have been called with the right url
    requests.get.assert_called_once_with(
        'https://api.github.com/repos/owner/project/hooks',
        headers={
            'Authorization': 'token fake-token'
        }
    )

    # And it should have returned the response
    result.should.equal([])


@patch('carpentry.models.Builder.delete_single_github_hook')
@patch('carpentry.models.Builder.list_github_hooks')
def test_buidler_cleanup_github_hooks(
        list_github_hooks,
        delete_single_github_hook):
    ('Builder.cleanup_github_hooks returns an empty '
     'list when failed')

    # Given list_github_hooks is mocked
    list_github_hooks.return_value = [
        {
            'config': {
                'missing': 'url',
                'intentionally': True,
            },
            'id': 11,
        },
        {
            'config': {
                'url': 'http://canary.is',
            },
            'id': 33,
        },
        {
            'config': {
                'url': 'http://localhost:5000/foo',
            },
            'id': 22,
        }
    ]

    # And an instance of builder with a valid github uri
    builder = Builder(
        git_uri='git@github.com:owner/project.git'
    )

    # When I call cleanup_github_hooks
    builder.cleanup_github_hooks('fake-token')

    # Then delete_single_github_hook was called appropriately
    delete_single_github_hook.assert_called_once_with(
        22,
        'fake-token'
    )

    # And list_github_hooks was called appropriately
    list_github_hooks.assert_called_once_with('fake-token')


@patch('carpentry.models.Builder.get_last_build')
@patch('carpentry.models.Builder.determine_github_repo_from_git_uri')
def test_builder_to_dict(
        determine_github_repo_from_git_uri,
        get_last_build):
    ('Builder.to_dict returns a very chubby dictionary')

    last_build = get_last_build.return_value
    last_build.to_dict.return_value = {
        'status': 'running'
    }

    determine_github_repo_from_git_uri.return_value = (
        'http://foo.io/bar.json')

    # Given an instance of builder with a valid github uri
    builder1 = Builder(
        name='The Awesome Pr0JName',
        git_uri='git@github.com:owner/project.git',
        status='success',
    )

    result = builder1.to_dict()
    result.should.equal({
        'id': None,
        'shell_script': None,
        'branch': None,
        'build_timeout_in_seconds': None,
        'creator_user_id': None,
        'css_status': 'success',
        'git_clone_timeout_in_seconds': None,
        'github_hook_data': None,
        'git_uri': 'git@github.com:owner/project.git',
        'github_hook_url': 'http://localhost:5000/api/hooks/None',
        'last_build': {
            'status': 'running'
        },
        'name': 'The Awesome Pr0JName',
        'slug': 'theawesomepr0jname',
        'status': 'success'
    })


def test_determine_github_repo_from_git_uri_failing():
    ('Builder.determine_github_repo_from_git_uri returns '
     'and empty dict when failed to match the regex')

    result = Builder.determine_github_repo_from_git_uri(
        'git@gogs.io:owner/project.git'
    )
    result.should.equal({})


def test_set_github_hook_cached():
    ('Builder.set_github_hook returns the cached values '
     'from the github_hook_data field')

    b1 = Builder(
        github_hook_data='{"foo": "bar"}'
    )
    result = b1.set_github_hook('fake-token')
    result.should.equal({'foo': 'bar'})


@patch('carpentry.models.Builder.save')
@patch('carpentry.models.requests')
def test_set_github_hook(requests, save):
    ('Builder.set_github_hook returns the cached values '
     'from the github_hook_data field')

    response = requests.post.return_value
    response.json.return_value = {'github': 'yay'}
    b1 = Builder(
        git_uri='git@github.com:gabrielfalcao/go-horse.git'
    )
    result = b1.set_github_hook('fake-token')
    result.should.equal({'github': 'yay'})

    save.assert_called_once_with()


@patch('carpentry.models.uuid')
@patch('carpentry.models.datetime')
@patch('carpentry.models.get_pipeline')
@patch('carpentry.models.Build')
def test_builder_trigger(Build, get_pipeline, datetime_mock, uuid_mock):
    ('Builder.trigger creates build and pushes it to '
     'the build pipeline')

    datetime_mock.datetime = datetime
    datetime_mock.date = date
    datetime_mock.time = time

    uuid_mock.UUID = uuid.UUID
    uuid_mock.uuid1.return_value = uuid.UUID(
        '4b1d90f0-96c2-40cd-9c21-35eee1f243d3')

    pipeline = get_pipeline.return_value

    build1 = Build.create.return_value
    build1.to_dict.return_value = {
        'foo': 'bar'
    }

    user = Mock(name='User(id=1)')
    user.to_dict.return_value = {'user': 1}

    builder1 = Builder(
        name='Awesome Project 1',
        git_uri='git@github.com:gabrielfalcao/go-horse.git'
    )
    result = builder1.trigger(
        user,
        'master',
        'commit-hash',
        'Gabriel Falcao',
        'gabriel@carpentry.io',
        '{"hook": "data"}',
    )
    pipeline.input.put.assert_called_once_with({
        'status': None,
        'css_status': 'success',
        'name': 'Awesome Project 1',
        'id_rsa_private': None,
        'build_timeout_in_seconds': None,
        'id_rsa_public': None,
        'shell_script': None,
        'git_clone_timeout_in_seconds': None,
        'slug': 'awesomeproject1',
        'git_uri': 'git@github.com:gabrielfalcao/go-horse.git',
        'github_hook_url': 'http://localhost:5000/api/hooks/None',
        'user': {'user': 1},
        'branch': None,
        'github_hook_data': None,
        'creator_user_id': None,
        'foo': 'bar',
        'id': None
    })


@patch('carpentry.models.Build')
def test_clear_builds(Build):
    ('Builder.clear_builds returns deletes the existing builds')

    build1 = Mock(name='build1')
    build2 = Mock(name='build2')
    Build.objects.filter.return_value = [
        build1,
        build2,
    ]

    builder = Builder(
        id=uuid.UUID('4b1d90f0-96c2-40cd-9c21-35eee1f243d3'),
    )
    result = builder.clear_builds()

    build1.delete.assert_called_once_with()
    build2.delete.assert_called_once_with()

    result.should.equal([build1, build2])
    Build.objects.filter.assert_called_once_with(
        builder_id=uuid.UUID('4b1d90f0-96c2-40cd-9c21-35eee1f243d3'),
    )


@patch('carpentry.models.Build')
def test_get_last_build(Build):
    ('Builder.get_last_build returns the last build')

    build1 = Mock(name='build1')
    build2 = Mock(name='build2')
    Build.objects.filter.return_value = [
        build1,
        build2,
    ]

    builder = Builder(
        id=uuid.UUID('4b1d90f0-96c2-40cd-9c21-35eee1f243d3'),
    )
    result = builder.get_last_build()

    result.should.equal(build1)


@patch('carpentry.models.Build')
def test_get_last_build_not_found(Build):
    ('Builder.get_last_build returns none if there are no builds')

    Build.objects.filter.return_value = []

    builder = Builder(
        id=uuid.UUID('4b1d90f0-96c2-40cd-9c21-35eee1f243d3'),
    )
    result = builder.get_last_build()

    result.should.be.none

# end of builder tests
#######################
