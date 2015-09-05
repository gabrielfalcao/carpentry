#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
from carpentry.models import Builder

from .helpers import safe_db


@safe_db
def test_create_builder(context):
    ('Creating builders in cassandra should work')
    # Given that I create a Builder
    builder = Builder.objects.create(
        id=uuid.uuid1(),
        name=u'Device Management [unit tests]',
        git_uri='git@github.com:gabrielfalcao/lettuce.git',
        shell_script='make test',
    )

    # When I get all results
    results = list(Builder.all())

    # Then it should have one result
    results.should.have.length_of(1)

    # And that one result should match the created Builder
    results[0].id.should.equal(builder.id)
