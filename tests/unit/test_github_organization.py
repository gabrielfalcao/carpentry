#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
from mock import patch
from carpentry.models import GithubOrganization

test_uuid = uuid.UUID('a1ea566e-5608-4670-a215-60bc34311c65')


@patch('carpentry.models.uuid')
@patch('carpentry.models.GithubOrganization.save')
def test_github_organization_store_one_from_dict(
        save, uuid_mock):
    ('GithubOrganization.store_one_from_dict() '
     'should break down the parameters and '
     'create save a GithubOrganization instance')
    uuid_mock.UUID = uuid.UUID
    uuid_mock.uuid1.return_value = test_uuid
    # Given a valid item
    item = {
        'id': '42',
        'login': 'gabrielfalcao',
        'avatar_url': 'fine',
        'url': 'you know',
        'html_url': 'you also know',
        'ssh_url': 'foo.com',
    }

    # When I call GithubOrganization.store_one_from_dict
    result = GithubOrganization.store_one_from_dict(item)

    # Then it should return an instance of
    result.should.be.a(GithubOrganization)

    # And it has the values well broken down
    result.to_dict(simple=True).should.equal({'avatar_url': 'fine', 'github_id': '42', 'html_url': 'you also know', 'id': uuid.UUID('a1ea566e-5608-4670-a215-60bc34311c65'), 'login': 'gabrielfalcao', 'response_data': '{"url": "you know", "html_url": "you also know", "avatar_url": "fine", "ssh_url": "foo.com", "login": "gabrielfalcao", "id": "42"}', 'url': 'you know'})
