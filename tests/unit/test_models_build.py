#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
import json
from mock import patch
from carpentry.models import Build


def test_build_author_gravatar_url():
    ('Build.author_gravatar_url returns a valid url')
    b = Build(author_email='foo@bar.com')
    b.author_gravatar_url.should.equal(
        'https://s.gravatar.com/avatar/f3ada405ce890b6f8204094deb12d8a8')


def test_build_url():
    ('Build.url returns a valid url')
    b = Build(
        id=uuid.UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'),
        author_email='foo@bar.com',
        builder_id=uuid.UUID('4b1d90f0-96c2-40cd-9c21-35eee1f243d3'),
    )
    b.url.should.equal(
        'http://localhost:5000/#/builder/4b1d90f0-96c2-40cd-9c21-35eee1f243d3/build/4b1d90f0-aaaa-40cd-9c21-35eee1f243d3')


def test_build_github_repo_info():
    ('Build.github_repo_info returns a valid url')
    b = Build(
        id=uuid.UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'),
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
        id=uuid.UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'),
        builder_id=uuid.UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'),
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
            "target_url": "http://localhost:5000/#/builder/4b1d90f0-aaaa-40cd-9c21-35eee1f243d3/build/4b1d90f0-aaaa-40cd-9c21-35eee1f243d3",
            "description": "some description",
            "context": "continuous-integration/carpentry"
        })
    )
    save.assert_called_once_with()


def test_build_to_dict():
    ('Build.to_dict returns a dict')
    b = Build(
        id=uuid.UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'),
        builder_id=uuid.UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'),
        git_uri='git@github.com:gabrielfalcao/lettuce.git',
        commit='commit1'
    )

    b.to_dict().should.equal({
        'author_email': None,
        'author_gravatar_url': 'https://s.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e',
        'author_name': None,
        'branch': None,
        'builder_id': '4b1d90f0-aaaa-40cd-9c21-35eee1f243d3',
        'code': None,
        'commit': 'commit1',
        'commit_message': None,
        'css_status': 'warning',
        'date_created': None,
        'date_finished': None,
        'docker_status': {},
        'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
        'github_repo_info': {
            'name': 'lettuce',
            'owner': 'gabrielfalcao'
        },
        'github_status_data': None,
        'github_webhook_data': None,
        'id': '4b1d90f0-aaaa-40cd-9c21-35eee1f243d3',
        'status': None,
        'stderr': None,
        'stdout': None,
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
    b = Build(builder_id=uuid.UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'))

    # When I check the .builder property
    b.builder.should.equal(Builder.get.return_value)

    # Then I see that it was retrieved using Builder.get(id=builder_id)
    Builder.get.assert_called_once_with(id=uuid.UUID('4b1d90f0-aaaa-40cd-9c21-35eee1f243d3'))


@patch('carpentry.models.Build.save')
@patch('carpentry.models.force_unicode')
def test_append_to_stdout(force_unicode, save_build):
    ("Build.append_to_stdout() appends the forced unicode string and")
    force_unicode.side_effect = lambda x: "[{0}]".format(x)

    # Given an instance of build that has some stdout string already
    b = Build(stdout='[beginning]')

    # When I call append_to_stdout
    b.append_to_stdout('end')

    # Then the stdout should have been concatenated with the result of force_unicode
    b.stdout.should.equal('[beginning][end]')

    # And Build.save was called
    save_build.assert_called_once_with()

    # And force_unicode was called with the given string
    force_unicode.assert_called_once_with('end')
