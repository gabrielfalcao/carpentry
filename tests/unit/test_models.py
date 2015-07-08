#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
from mock import patch
from datetime import datetime, date, time
from carpentry.models import serialize_value
from carpentry.models import get_pipeline
from carpentry.models import slugify
from carpentry.models import model_to_dict
from carpentry.models import GithubOrganization
from carpentry.workers import RunBuilder


def test_get_pipeline():
    ('carpentry.models.get_pipeline should return an instance of the RunBuilder pipeline')

    get_pipeline().should.be.a(RunBuilder)


def test_slugify():
    ('carpentry.models.slugify should return a slugified string')

    slugify("Carpentry CI").should.equal('carpentryci')


def test_serialize_value_object_to_dict():
    ('carpentry.models.serialize_value() should be able to serialize an object that responds to to_dict')

    class FooBar(object):
        def to_dict(self):
            return {
                'ohh': 'leh-leh'
            }

    foo = FooBar()
    serialize_value(foo).should.equal({
        'ohh': 'leh-leh'
    })


def test_serialize_value_datetime():
    ('carpentry.models.serialize_value() should be able to serialize datetime objects')

    foo1 = datetime(2015, 07, 07)
    foo2 = date(2015, 07, 07)
    foo3 = time(12, 24, 36)

    serialize_value(foo1).should.equal('2015-07-07 00:00:00')
    serialize_value(foo2).should.equal('2015-07-07')
    serialize_value(foo3).should.equal('12:24:36')


def test_serialize_value_uuid():
    ('carpentry.models.serialize_value() should be able to serialize uuid objects')

    foo = uuid.UUID('4b1d90f0-96c2-40cd-9c21-35eee1f243d3')

    serialize_value(foo).should.equal(
        '4b1d90f0-96c2-40cd-9c21-35eee1f243d3')


def test_serialize_value_anything_else():
    ('carpentry.models.serialize_value() should return the original '
     'value if it is not one of the handled cases')

    serialize_value('chuck-norris').should.equal('chuck-norris')


def test_serialize_model_to_dict():
    ('carpentry.models.model_to_dict() should return awesomeness')

    org = GithubOrganization(
        id=uuid.UUID('a1ea566e-5608-4670-a215-60bc34311c65'),
        login='chucknorris',
    )

    model_to_dict(org).should.equal({
        'avatar_url': None,
        'github_id': None,
        'html_url': None,
        'id': 'a1ea566e-5608-4670-a215-60bc34311c65',
        'login': 'chucknorris',
        'response_data': None,
        'url': None
    })
