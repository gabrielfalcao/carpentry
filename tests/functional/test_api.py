#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
import json
from jaci.models import Builder, JaciPreference, Build

from .helpers import api


@api
def test_create_builder(context):
    ('POST to /api/builder should create a builder')

    # When I prepare the headers for authentication
    context.headers.update({
        'Authorization': 'Bearer: testtoken'
    })

    # And I POST to /api/builders
    response = context.http.post(
        '/api/builder',
        data=json.dumps({
            'name': 'Device Management [unit tests]',
            'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
            'build_instructions': 'make test',
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
        'build_instructions': u'make test',
        'css_status': u'info',
        'git_uri': u'git@github.com:gabrielfalcao/lettuce.git',
        # 'id_rsa_private': u'the private key',
        # 'id_rsa_public': u'the public key',
        'last_build': None,
        'name': u'Device Management [unit tests]',
        'status': u'ready'
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
    builder.should.have.property('build_instructions').being.equal('make test')
    builder.should.have.property('id_rsa_private').being.equal('the private key')
    builder.should.have.property('id_rsa_public').being.equal('the public key')
    builder.should.have.property('status').being.equal('ready')


@api
def test_set_preferences(context):
    ('POST to /api/preferences should set multiple preferences')

    # When I prepare the headers for authentication
    context.headers.update({
        'Authorization': 'Bearer: testtoken'
    })

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
    results = list(JaciPreference.all())

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
        build_instructions='make test',
    )
    Builder.create(
        id=uuid.uuid1(),
        name=u'Builder 2',
        git_uri='2-git-url-one',
        build_instructions='make test',
    )
    Builder.create(
        id=uuid.uuid1(),
        name=u'Builder 3',
        git_uri='3-git-url-one',
        build_instructions='make test',
    )

    # When I prepare the headers for authentication
    context.headers.update({
        'Authorization': 'Bearer: testtoken'
    })

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
        build_instructions='make test',
    )

    # When I prepare the headers for authentication
    context.headers.update({
        'Authorization': 'Bearer: testtoken'
    })

    # And I PUT on /api/builders
    response = context.http.put(
        '/api/builder/{0}'.format(bd1.id),
        data=json.dumps({
            'build_instructions': 'make test',
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
        'name': 'Device Management [unit tests]',
        'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
        'build_instructions': 'make test',
        'status': 'ready',
        'branch': 'master',
        'last_build': None,
        'css_status': 'info',
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
    builder.should.have.property('build_instructions').being.equal('make test')
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
        build_instructions='make test',
    )

    # When I prepare the headers for authentication
    context.headers.update({
        'Authorization': 'Bearer: testtoken'
    })

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
        'branch': u'master',
        'build_instructions': u'make test',
        'css_status': u'info',
        'git_uri': u'git@github.com:gabrielfalcao/lettuce.git',
        'last_build': None,
        'name': u'Device Management [unit tests]',
        'status': u'ready'
    })
    builder_id.should_not.be.none

    # And it should be in the list of builders
    results = list(Builder.all())

    # Then it should have no results
    results.should.be.empty


@api
def test_create_build_instance_from_builder(context):
    ('POST to /api/builder/uuid/build should create a new build and scheduler it')

    # Given a builder that there are 3 builders
    bd1 = Builder.create(
        id=uuid.uuid1(),
        name='Device Management [unit tests]',
        git_uri='git@github.com:gabrielfalcao/lettuce.git',
        build_instructions='make test',
    )

    # When I prepare the headers for authentication
    context.headers.update({
        'Authorization': 'Bearer: testtoken'
    })

    # And I POST on /api/builder/uuid/build
    response = context.http.post(
        '/api/builder/{0}/build'.format(bd1.id),
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
        'status': 'scheduled',
        'branch': 'master',
        'code': None,
        'stdout': None,
        'stderr': None,
        'date_finished': None,
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
    build.should.have.property('status').being.equal('scheduled')
    build.should.have.property('builder_id')
    str(build.builder_id).should.be.equal(str(builder_id))
