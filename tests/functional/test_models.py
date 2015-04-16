#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import uuid
from datetime import datetime
from jaci.models import User, Post

from .helpers import safe_db


@safe_db
def test_create_user(context):
    ('Creating users in cassandra should work')
    # Given that I create a User
    user = User.create(
        id=uuid.uuid1(),
        name=u'Mary Doe',
        email='jd@gmail.com',
        password='123',
        date_added=datetime(1988, 2, 25)
    )

    # When I get all results
    results = list(User.all())

    # Then it should have one result
    results.should.have.length_of(1)

    # And that one result should match the created User
    results[0].id.should.equal(user.id)


@safe_db
def test_create_post(context):
    ('A user can create a post')

    # Given a User
    user = User.create(
        id=uuid.uuid1(),
        name=u'Mary Doe',
        email='jd@gmail.com',
        password='123',
        date_added=datetime(1988, 2, 25)
    )

    # When she creates a post
    post = user.create_post(
        title="foo bar",
        description="baz",
        body="The body",
        link="http://foo.bar",
    )

    # Then it should be in the list of posts
    results = list(Post.all())

    # Then it should have one result
    results.should.have.length_of(1)

    # And that one result should match the created Post
    results[0].id.should.equal(post.id)
    results[0].user_id.should.equal(user.id)
