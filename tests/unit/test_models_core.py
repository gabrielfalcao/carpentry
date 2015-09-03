#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
from mock import patch
from datetime import datetime, date, time
from carpentry.models import prepare_value_for_serialization
from carpentry.models import get_pipeline
from carpentry.models import slugify
from carpentry.models import model_to_dictionary
from carpentry.models import GithubOrganization
from carpentry.models import CarpentryBaseActiveRecord
from carpentry.workers import RunBuilder


@patch('carpentry.models.JSONRedisBackend')
def test_get_pipeline(JSONRedisBackend):
    ('carpentry.models.get_pipeline should return an instance of the RunBuilder pipeline')

    get_pipeline().should.be.a(RunBuilder)


def test_slugify():
    ('carpentry.models.slugify should return a slugified string')

    slugify("Carpentry CI").should.equal('carpentryci')


def test_prepare_value_for_serialization_object_to_dictionary():
    ('carpentry.models.prepare_value_for_serialization() should be able to serialize an object that responds to to_dictionary')

    class FooBar(object):

        def to_dictionary(self):
            return {
                'ohh': 'leh-leh'
            }

    foo = FooBar()
    prepare_value_for_serialization(foo).should.equal({
        'ohh': 'leh-leh'
    })


def test_prepare_value_for_serialization_datetime():
    ('carpentry.models.prepare_value_for_serialization() should be able to serialize datetime objects')

    foo1 = datetime(2015, 07, 07)
    foo2 = date(2015, 07, 07)
    foo3 = time(12, 24, 36)

    prepare_value_for_serialization(foo1).should.equal('2015-07-07 00:00:00')
    prepare_value_for_serialization(foo2).should.equal('2015-07-07')
    prepare_value_for_serialization(foo3).should.equal('12:24:36')


def test_prepare_value_for_serialization_uuid():
    ('carpentry.models.prepare_value_for_serialization() should be able to serialize uuid objects')

    foo = uuid.UUID('4b1d90f0-96c2-40cd-9c21-35eee1f243d3')

    prepare_value_for_serialization(foo).should.equal(
        '4b1d90f0-96c2-40cd-9c21-35eee1f243d3')


def test_prepare_value_for_serialization_anything_else():
    ('carpentry.models.prepare_value_for_serialization() should return the original '
     'value if it is not one of the handled cases')

    prepare_value_for_serialization(
        'chuck-norris').should.equal('chuck-norris')


def test_serialize_model_to_dictionary():
    ('carpentry.models.model_to_dictionary() should return awesomeness')

    org = GithubOrganization(
        id=uuid.UUID('a1ea566e-5608-4670-a215-60bc34311c65'),
        login='chucknorris',
    )

    model_to_dictionary(org).should.equal({
        'avatar_url': '',
        'github_id': 0,
        'html_url': '',
        'id': 'a1ea566e-5608-4670-a215-60bc34311c65',
        'login': 'chucknorris',
        'response_data': '',
        'url': ''
    })
