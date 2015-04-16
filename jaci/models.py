# -*- coding: utf-8 -*-
#
import re
import uuid
import bcrypt
import logging
from dateutil.parser import parse as parse_datetime
from datetime import datetime
from cqlengine import columns
from cqlengine.models import Model
from jaci.server import get_absolute_url


def slugify(string):
    return re.sub(r'\W+', '', string)


class NewsletterSubscription(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    name = columns.Text()
    email = columns.Text(index=True)
    date_created = columns.DateTime()

    @classmethod
    def subscribe(cls, name, email):
        try:
            return cls.create(
                id=uuid.uuid1(),
                name=name or email,
                email=email,
                date_created=datetime.utcnow()
            )
        except Exception:
            logging.exception('Failed to subscribe name:%s email:%s', name, email)


class UserToken(Model):
    user_id = columns.TimeUUID(partition_key=True, primary_key=True)
    token = columns.Text(index=True, partition_key=True)
    date_created = columns.DateTime()


class User(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    name = columns.Text()
    email = columns.Text(index=True)
    password = columns.Text()
    date_added = columns.DateTime()
    point_delta = columns.Float()

    @classmethod
    def encrypt_password(self, password):
        result = bcrypt.hashpw(password, bcrypt.gensalt())
        return result

    @classmethod
    def authenticate(cls, email, given_password):
        user = cls.objects.filter(email=email).get()
        if not user:
            logging.error('Could not authenticate, user not found: %s', email)
            return

        password = given_password.encode('utf-8')
        hashed = user.password.encode('utf-8')
        if bcrypt.hashpw(password, hashed) == hashed:
            result = UserToken.create(
                token=str(uuid.uuid4()),
                date_created=datetime.utcnow(),
                user_id=user.id
            )
            return result

    def create_post(self, title, slug=None, description=None, body=None, link=None, date_published=None):
        if not slug:
            slug = slugify(title)

        if isinstance(date_published, basestring):
            date_published = parse_datetime(date_published)
        elif date_published is None:
            date_published = datetime.utcnow()

        return Post.create(
            id=uuid.uuid1(),
            user_id=self.id,
            title=title,
            slug=slug,
            description=description,
            body=body,
            link=link,
            date_added=datetime.utcnow(),
            date_published=date_published,
        )

    def get_post(self, uuid):
        post = Post.get(id=uuid, user_id=self.id)
        return post

    def delete_post(self, uuid):
        post = self.get_post(uuid)
        if post:
            post.delete()
        return post

    def edit_post(self, uuid, data):
        post = self.get_post(uuid)
        if not post:
            return False

        for key, value in data.items():
            if value is None:
                continue
            setattr(post, key, value)

        post.save()
        return post


class Post(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    user_id = columns.TimeUUID(partition_key=True, index=True)
    title = columns.Text()
    slug = columns.Text(index=True)
    description = columns.Text()
    main_image = columns.Text()
    tags = columns.Text()
    body = columns.Text()
    link = columns.Text(index=True)
    date_published = columns.DateTime(primary_key=True)
    date_added = columns.DateTime(index=True)
    last_edited = columns.DateTime(index=True)

    def get_url(self):
        return get_absolute_url('/api/post/{0}'.format(self.id))

    def to_dict(self):
        return dict(self.items())
