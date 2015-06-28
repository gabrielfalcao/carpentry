#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
import json
from carpentry.models import Builder, CarpentryPreference, Build

from .helpers import api


@api
def test_create_builder(context):
    ('POST to /api/builder should create a builder')

    context.github.on_post(
        path='/repos/gabrielfalcao/lettuce/hooks',
        body=json.dumps({
            'hook_set': True
        })
    )

    context.github.on_get(
        path='/repos/gabrielfalcao/lettuce/hooks',
        body=json.dumps([
            {
                'id': 'hookid1',
                'config': {
                    'url': 'https://carpentry.io/hookid1'
                }
            }
        ])
    )

    context.github.on_delete(
        path='/repos/gabrielfalcao/lettuce/hook/hookid1',
        body=json.dumps({'msg': 'hook deleted successfully'})
    )

    # Given that I POST to /api/builders
    response = context.http.post(
        '/api/builder',
        data=json.dumps({
            'name': 'Device Management [unit tests]',
            'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
            'shell_script': 'make test',
            'id_rsa_private': 'the private key',
            'id_rsa_public': 'the public key',
        }),
        headers=context.headers,
    )

    # Then the response should be 200
    response.status_code.should.equal(200)

    # And it should be a json
    data = json.loads(response.data)
    builder_id = data.pop('id', None)
    data.should.equal({
        u'branch': u'master',
        u'css_status': u'success',
        u'git_uri': u'git@github.com:gabrielfalcao/lettuce.git',
        u'id_rsa_private': u'the private key',
        u'id_rsa_public': u'the public key',
        u'last_build': None,
        u'name': u'Device Management [unit tests]',
        u'shell_script': u'make test',
        u'slug': u'devicemanagementunittests',
        u'status': u'ready',
        u'github_hook_data': None,
        u'creator_user_id': unicode(context.user.id),
    })
    builder_id.should_not.be.none

    # And it should be in the list of builders
    results = list(Builder.all())

    # Then it should have one result
    results.should.have.length_of(1)

    # And that one result should match the created Builder
    builder = results[0]
    builder.should.have.property('name').being.equal('Device Management [unit tests]')
    builder.should.have.property('git_uri').being.equal('git@github.com:gabrielfalcao/lettuce.git')
    builder.should.have.property('shell_script').being.equal('make test')
    builder.should.have.property('id_rsa_private').being.equal('the private key')
    builder.should.have.property('id_rsa_public').being.equal('the public key')
    builder.should.have.property('status').being.equal('ready')


@api
def test_set_preferences(context):
    ('POST to /api/preferences should set multiple preferences')


    # And I POST to /api/builders
    response = context.http.post(
        '/api/preferences',
        data=json.dumps({
            'docker_registry_url': 'https://docker.cnry.io',
            'global_id_rsa_private_key': 'the private key',
            'global_id_rsa_public_key': 'the public key',
        }),
        headers=context.headers,
    )

    # Then the response should be 200
    response.status_code.should.equal(200)

    # And it should be a json
    data = json.loads(response.data)
    data.should.equal({
        'docker_registry_url': 'https://docker.cnry.io',
        'global_id_rsa_private_key': 'the private key',
        'global_id_rsa_public_key': 'the public key',
    })

    # And it should be in the list of preferences
    results = list(CarpentryPreference.all())

    # Then it should have one result
    results.should.have.length_of(3)


@api
def test_list_builders(context):
    ('GET on /api/builders should list existing builders')

    # Givent that there are 3 builders
    Builder.create(
        id=uuid.uuid1(),
        name=u'Builder 1',
        git_uri='1-git-url-one',
        shell_script='make test',
    )
    Builder.create(
        id=uuid.uuid1(),
        name=u'Builder 2',
        git_uri='2-git-url-one',
        shell_script='make test',
    )
    Builder.create(
        id=uuid.uuid1(),
        name=u'Builder 3',
        git_uri='3-git-url-one',
        shell_script='make test',
    )


    # And I GET on /api/builders
    response = context.http.get(
        '/api/builders',
        headers=context.headers,
    )

    # Then the response should be 200
    response.status_code.should.equal(200)

    # And it should be a json
    data = json.loads(response.data)
    data.should.be.a(list)
    data.should.have.length_of(3)

    # And there are also 3 items in the database
    Builder.objects.all().should.have.length_of(3)


@api
def test_edit_builder(context):
    ('PUT to /api/builder should edit a builder')

    # Given a builder that there are 3 builders
    bd1 = Builder.create(
        id=uuid.uuid1(),
        name='Device Management [unit tests]',
        git_uri='git@github.com:gabrielfalcao/lettuce.git',
        shell_script='make test',
    )

    # And I PUT on /api/builders
    response = context.http.put(
        '/api/builder/{0}'.format(bd1.id),
        data=json.dumps({
            'shell_script': 'make test',
            'id_rsa_private': 'the private key',
            'id_rsa_public': 'the public key',
        }),
        headers=context.headers,
    )

    # Then the response should be 200
    response.status_code.should.equal(200)

    # And it should be a json
    data = json.loads(response.data)
    builder_id = data.pop('id', None)
    data.should.equal({
        'branch': u'master',
        'css_status': u'success',
        'git_uri': u'git@github.com:gabrielfalcao/lettuce.git',
        'id_rsa_private': u'the private key',
        'id_rsa_public': u'the public key',
        'last_build': None,
        'name': u'Device Management [unit tests]',
        'shell_script': u'make test',
        'slug': u'devicemanagementunittests',
        'status': u'ready',
        'github_hook_data': None,
        'creator_user_id': None
    })
    builder_id.should_not.be.none

    # And it should be in the list of builders
    results = list(Builder.all())

    # Then it should have one result
    results.should.have.length_of(1)

    # And that one result should match the edited Builder
    builder = results[0]
    builder.should.have.property('name').being.equal('Device Management [unit tests]')
    builder.should.have.property('git_uri').being.equal('git@github.com:gabrielfalcao/lettuce.git')
    builder.should.have.property('shell_script').being.equal('make test')
    builder.should.have.property('id_rsa_private').being.equal('the private key')
    builder.should.have.property('id_rsa_public').being.equal('the public key')
    builder.should.have.property('status').being.equal('ready')


@api
def test_delete_builder(context):
    ('DELETE to /api/builder should delete a builder')

    # Given a builder that there are 3 builders
    bd1 = Builder.create(
        id=uuid.uuid1(),
        name='Device Management [unit tests]',
        git_uri='git@github.com:gabrielfalcao/lettuce.git',
        shell_script='make test',
        creator_user_id=context.user.id
    )

    # And I DELETE to /api/builders
    response = context.http.delete(
        '/api/builder/{0}'.format(bd1.id),
        headers=context.headers,
    )

    # Then the response should be 200
    response.status_code.should.equal(200)

    # And it should be a json
    data = json.loads(response.data)
    builder_id = data.pop('id', None)
    data.should.equal({
        u'branch': u'master',
        u'css_status': u'success',
        u'git_uri': u'git@github.com:gabrielfalcao/lettuce.git',
        u'id_rsa_private': None,
        u'id_rsa_public': None,
        u'last_build': None,
        u'name': u'Device Management [unit tests]',
        u'shell_script': u'make test',
        u'slug': u'devicemanagementunittests',
        u'status': u'ready',
        'github_hook_data': None,
        'creator_user_id': unicode(context.user.id)
    })
    builder_id.should_not.be.none

    # And it should be in the list of builders
    results = list(Builder.all())

    # Then it should have no results
    results.should.be.empty


@api
def test_create_build_instance_from_builder(context):
    ('POST to /api/builder/uuid/build should create a new build and scheduler it')

    context.github.on_post(
        path='/repos/gabrielfalcao/lettuce/hooks',
        body=json.dumps({
            'hook_set': True
        })
    )

    # Given a builder that there are 3 builders
    bd1 = Builder.create(
        id=uuid.uuid1(),
        name='Device Management [unit tests]',
        git_uri='git@github.com:gabrielfalcao/lettuce.git',
        shell_script='make test',
    )

    # And I POST on /api/builder/uuid/build
    response = context.http.post(
        '/api/builder/{0}/build'.format(bd1.id),
        data=json.dumps({
            'author_name': 'Gabriel',
            'author_email': 'gabriel@nacaolivre.org',
            'commit': 'oooo',
        }),
        headers=context.headers,
    )

    # Then the response should be 200
    response.status_code.should.equal(200)

    # And it should be a json
    data = json.loads(response.data)
    build_id = data.pop('id', None)
    builder_id = data.pop('builder_id', None)
    date_created = data.pop('date_created', None)
    data.should.equal({
        u'author_email': u'gabriel@nacaolivre.org',
        u'author_name': u'Gabriel',
        u'branch': u'master',
        u'code': None,
        u'commit': None,
        u'css_status': u'success',
        u'date_finished': None,
        u'status': u'ready',
        u'stderr': None,
        u'stdout': None,
        u'github_status_data': None
    })
    build_id.should_not.be.none
    date_created.should_not.be.none

    # And it should be in the list of builders
    results = list(Build.all())

    # Then it should have one result
    results.should.have.length_of(1)

    # And that one result should match the edited Builder
    build = results[0]
    builder_id.should.equal(str(bd1.id))
    build.should.have.property('stderr').being.equal(None)
    build.should.have.property('stdout').being.equal(None)
    build.should.have.property('code').being.equal(None)
    build.should.have.property('status').being.equal('ready')
    build.should.have.property('builder_id')
    str(build.builder_id).should.be.equal(str(builder_id))
