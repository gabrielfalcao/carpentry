#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
from uuid import UUID
import json
from datetime import datetime
from mock import patch
from carpentry.models import Build, Builder


STUB_BUILDER = Builder(
    id=UUID('4b1d90f0-96c2-40cd-9c21-35eee1f243d3'),
    name=u'Device Management [unit tests]',
    git_uri='git@github.com:gabrielfalcao/lettuce.git',
    shell_script='make test',
)


def test_build_author_gravatar_url():
    ('Build.author_gravatar_url returns a valid url')
    b = Build(author_email='foo@bar.com')
    b.author_gravatar_url.should.equal(
        'https://s.gravatar.com/avatar/f3ada405ce890b6f8204094deb12d8a8')


def test_build_url():
    ('Build.url returns a valid url')
    b = Build(
        id=UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'),
        author_email='foo@bar.com',
        builder=Builder(
            id=UUID('4b1d90f0-96c2-40cd-9c21-35eee1f243d3'),
            name=u'Device Management [unit tests]',
            git_uri='git@github.com:gabrielfalcao/lettuce.git',
            shell_script='make test',
        )
    )
    b.url.should.equal(
        'http://localhost:5000/#/builder/4b1d90f0-96c2-40cd-9c21-35eee1f243d3/build/4b1d90f0-aaaa-40cd-9c21-35eee1f243d3')


def test_build_github_repo_info():
    ('Build.github_repo_info returns a valid url')
    b = Build(
        id=UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'),
        git_uri='git@github.com:gabrielfalcao/lettuce.git',

    )
    b.github_repo_info.should.equal({
        'name': 'lettuce',
        'owner': 'gabrielfalcao'
    })


@patch('carpentry.models.Build.save')
@patch('carpentry.models.requests')
def test_build_set_github_status(requests, save):
    ('Build.github_repo_info returns a valid url')
    b = Build(
        id=UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'),
        builder=STUB_BUILDER,
        git_uri='git@github.com:gabrielfalcao/lettuce.git',
        commit='commit1'
    )

    b.set_github_status(
        'fake-token',
        'success',
        'some description',
    )

    requests.post.assert_called_once_with(
        'https://api.github.com/repos/gabrielfalcao/lettuce/statuses/commit1',
        headers={'Authorization': 'token fake-token'},
        data=json.dumps({
            "state": "success",
            "target_url": "http://localhost:5000/#/builder/4b1d90f0-96c2-40cd-9c21-35eee1f243d3/build/4b1d90f0-aaaa-40cd-9c21-35eee1f243d3",
            "description": "some description",
            "context": "continuous-integration/carpentry"
        })
    )
    save.assert_called_once_with()


def test_build_to_dictionary():
    ('Build.to_dictionary returns a dict')

    b = Build(
        id=UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'),
        builder=STUB_BUILDER,
        git_uri='git@github.com:gabrielfalcao/lettuce.git',
        commit='commit1',
        date_created=datetime(2015, 9, 1),
        date_finished=datetime(2015, 9, 2),
    )

    b.to_dictionary().should.equal({
        'author_email': u'',
        'author_gravatar_url': 'https://s.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e',
        'author_name': u'',
        'branch': u'',
        'builder': {
            'branch': u'',
            'build_timeout_in_seconds': 0,
            'creator': None,
            'git_clone_timeout_in_seconds': 0,
            'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
            'github_hook_data': u'',
            'id': UUID('4b1d90f0-96c2-40cd-9c21-35eee1f243d3'),
            'id_rsa_private': u'',
            'id_rsa_public': u'',
            'json_instructions': u'',
            'name': u'Device Management [unit tests]',
            'shell_script': 'make test',
            'status': u''
        },
        'code': 0,
        'commit': 'commit1',
        'commit_message': u'',
        'css_status': 'warning',
        'date_created': '2015-09-01 00:00:00',
        'date_finished': '2015-09-02 00:00:00',
        'docker_status': {},
        'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
        'github_repo_info': {
            'name': 'lettuce',
            'owner': 'gabrielfalcao'
        },
        'github_status_data': u'',
        'github_webhook_data': u'',
        'id': '4b1d90f0-aaaa-40cd-9c21-35eee1f243d3',
        'status': u'',
        'stderr': u'',
        'stdout': u''
    })


def test_github_status_info_ok():
    ('Build.github_status_info should return the deserialized json when available')

    b = Build(github_status_data=json.dumps({'hello': 'world'}))
    b.github_status_info.should.equal({
        'hello': 'world'
    })


def test_github_status_info_failed():
    ('Build.github_status_info should return an empty dict when failed')

    b = Build()
    b.github_status_info.should.be.a(dict)
    b.github_status_info.should.be.empty


def test_set_github_status_invalid():
    ('Build.set_github_status raises ValueError when the status is invalid')

    b = Build()
    b.set_github_status.when.called_with('test-token', 'unknownstatus', 'description').should.have.raised(
        ValueError,
        'Build.set_github_status got an invalid status: unknownstatus our of the options pending. success. error. failure'
    )


@patch('carpentry.models.Builder')
def test_builder_property(Builder):
    "Build.builder returns the parent builder model instance"

    # Given an instance of build that has a builder_id
    b = Build(builder=STUB_BUILDER)

    # When I check the .builder property
    b.builder.should.equal(STUB_BUILDER)


@patch('carpentry.models.Build.append_to_bytestream')
def test_append_to_stdout(append_to_bytestream):
    ("Build.append_to_stdout() appends the forced unicode string and")

    # Given an instance of build that has some stdout string already
    b = Build(
        stdout='[beginning]',
        git_uri='git@github.com:gabrielfalcao/lettuce.git'
    )

    # When I call append_to_stdout
    b.append_to_stdout('end')

    # And Build.append_to_bytestream was called
    append_to_bytestream.assert_called_once_with('stdout', 'end')


@patch('carpentry.models.Build.save')
def test_set_status_notoken(save_build):
    ('Build.set_status should just change the build status and save it')

    # Given a build instance
    b = Build()

    # When I call set_status
    b.set_status('failed')

    # Then save_build should have been called
    save_build.assert_called_once_with()

    # And the status should have been set
    b.status.should.equal('failed')


@patch('carpentry.models.Builder.get')
@patch('carpentry.models.Build.set_github_status')
@patch('carpentry.models.Build.save')
def test_set_status_github(save_build,
                           set_github_status,
                           get_builder):
    ('Build.set_status should also set the github status')
    parent_builder = get_builder.return_value

    # Given a build instance
    b = Build()

    # When I call set_status with an unknown status
    b.set_status('unknown', 'oops', 'test-token')

    # Then save_build should have been called
    save_build.assert_called_once_with()

    # And the status should have been set
    b.status.should.equal('unknown')

    # And set_github_status should have been called
    set_github_status.assert_called_once_with(
        'test-token',
        'pending',
        'oops'
    )


@patch('carpentry.models.Builder.save')
@patch('carpentry.models.Builder.get')
def test_build_save(get_builder, base_save):
    ('Build.save should set the status of the '
     'parent builder as well')
    parent_builder = Builder(
        id=UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'),
        name=u'Device Management [unit tests]',
        git_uri='git@github.com:gabrielfalcao/lettuce.git',
        shell_script='make test',
        status='ready',
    )
    get_builder.return_value = parent_builder

    # Given a build instance
    b = Build(
        status='success',
        builder=parent_builder
    )
    b.save()

    parent_builder.status.should.equal('success')
    parent_builder.save.assert_called_once_with()


def test_build_to_dictionary_bad_docker_status():
    ('Build.save should set the status of the '
     'parent builder as well')
    brid = UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3')

    # Given a build instance
    b = Build(
        docker_status='B@D',
        status='success',
        builder_id=brid,
        git_uri='git@github.com:gabrielfalcao/lettuce.git',
        date_created='',
        date_finished='',
    )

    b.to_dictionary().should.equal({
        'author_email': u'',
        'author_gravatar_url': 'https://s.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e',
        'author_name': u'',
        'branch': u'',
        'builder': None,
        'code': 0,
        'commit': u'',
        'commit_message': u'',
        'css_status': 'warning',
        'date_created': None,
        'date_finished': None,
        'docker_status': {},
        'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
        'github_repo_info': {
            'name': 'lettuce',
            'owner': 'gabrielfalcao'
        },
        'github_status_data': u'',
        'github_webhook_data': u'',
        'id': '',
        'status': 'success',
        'stderr': u'',
        'stdout': u''
    })


@patch('carpentry.models.Build.save')
def test_register_docker_status_json_ok(save_build):
    ('Build.register_docker_status sets the docker_status and saves when receiving a valid json')
    brid = UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3')

    # Given a build instance
    b = Build(
        docker_status='B@D',
        status='success',
        builder_id=brid,
        git_uri='git@github.com:gabrielfalcao/lettuce.git'
    )

    b.register_docker_status('{"foo":"bar"}')
    b.docker_status.should.equal('{"foo":"bar"}')
    save_build.assert_called_once_with()


@patch('carpentry.models.Build.append_to_stdout')
@patch('carpentry.models.Build.save')
def test_register_docker_status_json_failing(save_build, append_to_stdout):
    ('Build.register_docker_status skips setting the status '
     'when the given line is not a json object')
    brid = UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3')

    # Given a build instance
    b = Build(
        docker_status='B@D',
        status='success',
        builder_id=brid,
        git_uri='git@github.com:gabrielfalcao/lettuce.git'
    )

    b.register_docker_status('amor')
    b.docker_status.should.equal('B@D')

    append_to_stdout.assert_called_once_with('amor')
    save_build.called.should.be.false
