#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
from mock import patch, call
from carpentry.models import GithubRepository

test_uuid = uuid.UUID('a1ea566e-5608-4670-a215-60bc34311c65')


@patch('carpentry.models.uuid')
@patch('carpentry.models.GithubRepository.save')
@patch('carpentry.models.GithubOrganization')
def test_github_repository_store_one_from_dict(
        GithubOrganization, save, uuid_mock):
    ('GithubRepository.store_one_from_dict() '
     'should break down the parameters and '
     'create save a GithubRepository instance')
    uuid_mock.UUID = uuid.UUID
    uuid_mock.uuid1.return_value = test_uuid
    # Given a valid item
    item = {
        'name': 'sure',
        'ssh_url': 'git@github.com:gabrielfalcao/sure.it',
        'owner': {
            'login': 'gabrielfalcao'
        }
    }

    # When I call GithubRepository.store_one_from_dict
    result = GithubRepository.store_one_from_dict(item)

    # Then it should return an instance of
    result.should.be.a(GithubRepository)

    # And it has the values well broken down
    result.to_dict().should.equal({
        'git_uri': 'git@github.com:gabrielfalcao/sure.it',
        'id': 'a1ea566e-5608-4670-a215-60bc34311c65',
        'name': 'sure',
        'owner': 'gabrielfalcao',
        'response_data': '{"owner": {"login": "gabrielfalcao"}, "name": "sure", "ssh_url": "git@github.com:gabrielfalcao/sure.it"}'
    })

    GithubOrganization.store_one_from_dict.assert_called_once_with({
        'login': 'gabrielfalcao'
    })


@patch('carpentry.models.GithubRepository.store_one_from_dict')
def test_store_many_from_list(store_one_from_dict):
    ('GithubRepository.store_many_from_list should '
     'call store_one_from_dict for each item in the given list')

    # When I call GithubRepository.store_one_from_dict
    result = GithubRepository.store_many_from_list([
        'one',
        'two'
    ])

    store_one_from_dict.assert_has_calls([
        call('one'),
        call('two'),
    ])

    result.should.have.length_of(2)
