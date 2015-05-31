#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
import json
from jaci.models import Builder, JaciPreference

from .helpers import api


@api
def test_create_builder(context):
    ('POST to /api/builder should create a builder')

    # When I prepare the headers for authentication
    context.headers.update({
        'Authorization': 'Bearer: testtoken'
    })

    # And I BUILDER to /api/builders
    response = context.http.post(
        '/api/builder',
        data=json.dumps({
            'name': 'Device Management [unit tests]',
            'git_url': 'git@github.com:gabrielfalcao/lettuce.git',
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
        'name': 'Device Management [unit tests]',
        'git_url': 'git@github.com:gabrielfalcao/lettuce.git',
        'shell_script': 'make test',
        'id_rsa_private': 'the private key',
        'id_rsa_public': 'the public key',
        'status': 'ready',
    })
    builder_id.should_not.be.none

    # And it should be in the list of builders
    results = list(Builder.all())

    # Then it should have one result
    results.should.have.length_of(1)

    # And that one result should match the created Builder
    builder = results[0]
    builder.should.have.property('name').being.equal('Device Management [unit tests]')
    builder.should.have.property('git_url').being.equal('git@github.com:gabrielfalcao/lettuce.git')
    builder.should.have.property('shell_script').being.equal('make test')
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

    # And I BUILDER to /api/builders
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
        git_url='1-git-url-one',
        shell_script='make test',
    )
    Builder.create(
        id=uuid.uuid1(),
        name=u'Builder 2',
        git_url='2-git-url-one',
        shell_script='make test',
    )
    Builder.create(
        id=uuid.uuid1(),
        name=u'Builder 3',
        git_url='3-git-url-one',
        shell_script='make test',
    )

    # When I prepare the headers for authentication
    context.headers.update({
        'Authorization': 'Bearer: testtoken'
    })

    # And I BUILDER to /api/builders
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
