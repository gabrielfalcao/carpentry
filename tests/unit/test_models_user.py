#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
from mock import patch, Mock
from carpentry.models import User

test_uuid = uuid.UUID('a1ea566e-5608-4670-a215-60bc34311c65')


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


@patch('carpentry.models.User.get_github_metadata')
def test_user_to_dict(get_github_metadata):
    ('User.to_dict() should return the github metadata')

    get_github_metadata.return_value = {
        'login': 'Norris'
    }

    u = User(name='Chuck')

    u.to_dict().should.equal({
        'carpentry_token': None,
        'email': None,
        'github': {
            'login': 'Norris'
        },
        'github_access_token': None,
        'github_metadata': None,
        'id': None,
        'name': 'Chuck'
    })


@patch('carpentry.models.User.save')
@patch('carpentry.models.uuid')
def test_user_reset_token(uuid_mock, save_user):
    ('User.reset_token() should set the carpentry_token '
     'to a new uuid4()')

    uuid_mock.uuid4.return_value = test_uuid

    u = User(name='Chuck')

    u.reset_token()

    u.carpentry_token.should.equal(test_uuid)

    save_user.assert_called_once_with()


@patch('carpentry.models.User.objects')
def test_from_carpentry_token(user_objects):
    ('User.from_carpentry_token() should set the '
     'carpentry_token to a new uuid4()')

    user1 = Mock(name='user1')

    user_objects.filter.return_value = [user1]

    u = User.from_carpentry_token(test_uuid)

    u.should.equal(user1)


@patch('carpentry.models.User.objects')
def test_from_carpentry_token_no_token(user_objects):
    ('User.from_carpentry_token() should return '
     'None if no token is returned')

    u = User.from_carpentry_token('')

    u.should.be.none


@patch('carpentry.models.User.prepare_github_request_headers')
@patch('carpentry.models.requests')
def test_retrieve_organization_repos(
        requests,
        prepare_github_request_headers):
    ('User.retrieve_organization_repos() should return '
     'a list of repos')
    response = requests.get.return_value
    response.status_code = 200
    response.json.return_value = [
        'the', 'response',
    ]

    prepare_github_request_headers.return_value = {
        'has_headers': True
    }

    u = User()

    result = u.retrieve_organization_repos('sure')

    result.should.equal(['the', 'response'])
    requests.get.assert_called_once_with(
        'https://api.github.com/orgs/sure/repos',
        headers={
            'has_headers': True
        }
    )


@patch('carpentry.models.User.prepare_github_request_headers')
@patch('carpentry.models.requests')
def test_retrieve_organization_repos_failed(
        requests,
        prepare_github_request_headers):
    ('User.retrieve_organization_repos() should and empty list when failed')
    response = requests.get.return_value
    response.status_code = 400

    prepare_github_request_headers.return_value = {
        'has_headers': True
    }

    u = User()

    result = u.retrieve_organization_repos('sure')

    result.should.be.empty


@patch('carpentry.models.User.prepare_github_request_headers')
@patch('carpentry.models.requests')
def test_retrieve_user_repos(
        requests,
        prepare_github_request_headers):
    ('User.retrieve_user_repos() should return '
     'a list of repos')
    response = requests.get.return_value
    response.status_code = 200
    response.json.return_value = [
        'the', 'response',
    ]

    prepare_github_request_headers.return_value = {
        'has_headers': True
    }

    u = User()

    result = u.retrieve_user_repos()

    result.should.equal(['the', 'response'])
    requests.get.assert_called_once_with(
        'https://api.github.com/user/repos',
        headers={
            'has_headers': True
        }
    )


@patch('carpentry.models.User.prepare_github_request_headers')
@patch('carpentry.models.requests')
def test_retrieve_user_repos_failed(
        requests,
        prepare_github_request_headers):
    ('User.retrieve_user_repos() should and empty list when failed')
    response = requests.get.return_value
    response.status_code = 400

    prepare_github_request_headers.return_value = {
        'has_headers': True
    }

    u = User()

    result = u.retrieve_user_repos()

    result.should.be.empty


@patch('carpentry.models.GithubRepository')
@patch('carpentry.models.User.retrieve_user_repos')
@patch('carpentry.models.User.retrieve_organization_repos')
def test_retrieve_and_cache_github_repositories(
        retrieve_organization_repos,
        retrieve_user_repos,
        GithubRepository):
    ('User.retrieve_and_cache_github_repositories() should '
     '')
    retrieve_organization_repos.return_value = [
        {
            'owner': 'cnry',
            'name': 'bng1',
        }
    ]
    retrieve_user_repos.return_value = [
        {
            'owner': 'gabrielfalcao',
            'name': 'carpentry',
        }
    ]
    u = User()

    result = u.retrieve_and_cache_github_repositories()

    result.should.equal([
        {
            'owner': 'cnry',
            'name': 'bng1'
        },
        {
            'owner': 'gabrielfalcao',
            'name': 'carpentry'
        },
    ])


@patch('carpentry.models.User.save')
@patch('carpentry.models.User.get_github_metadata')
@patch('carpentry.models.requests')
def test_retrieve_github_organizations(
        requests,
        get_github_metadata,
        save_user):
    ('User.retrieve_github_organizations() should return '
     'a list of repos')

    get_github_metadata.return_value = {

    }
    response = requests.get.return_value
    response.status_code = 200
    response.json.return_value = [
        'the', 'response',
    ]

    u = User(
        github_access_token='thetoken',
    )

    result = u.retrieve_github_organizations()

    result.should.equal(['the', 'response'])
    requests.get.assert_called_once_with(
        'https://api.github.com/user/orgs',
        headers={
            'Authorization': 'token thetoken'
        }
    )

    save_user.assert_called_once_with()


@patch('carpentry.models.User.save')
@patch('carpentry.models.User.get_github_metadata')
@patch('carpentry.models.requests')
def test_retrieve_github_organizations_cached(
        requests,
        get_github_metadata,
        save_user):
    ('User.retrieve_github_organizations() should return '
     'a list of repos')

    get_github_metadata.return_value = {
        'organizations': ['cnry']
    }
    response = requests.get.return_value
    response.status_code = 200
    response.json.return_value = [
        'the', 'response',
    ]

    u = User(
        github_access_token='thetoken',
    )

    u.organizations.should.equal(['cnry'])


@patch('carpentry.models.User.retrieve_github_organizations')
@patch('carpentry.models.requests')
def test_organization_names(
        requests,
        retrieve_github_organizations):
    ('User.organization_names returns a list of all github organizations')
    retrieve_github_organizations.return_value = [
        {'login': 'cnry'}
    ]
    u = User()

    u.organization_names.should.equal(['cnry'])
