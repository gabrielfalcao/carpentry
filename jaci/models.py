# -*- coding: utf-8 -*-
#
import re
import redis
import uuid
import requests
# import bcrypt
import logging
import datetime
# from dateutil.parser import parse as parse_datetime
from lineup import JSONRedisBackend

from cqlengine import columns
from cqlengine.models import Model
from jaci import conf

logger = logging.getLogger('jaci')

BUILD_STATUSES = [
    'ready',      # no builds scheduled
    'scheduled',  # scheduled but not yet running
    'retrieving',    # git clone
    'checking',    # looking for .jaci.yml
    'preparing',    # preparing shell script
    'running',    # running
    'succeeded',  # finished with success, subprocess returned status 0
    'failed',     # finished with an error, subprocess returned status != 0
]


STATUS_MAP = {
    'ready': 'active',
    'succeeded': 'success',
    'failed': 'danger',
    'retrieving': 'info',
    'running': 'active',
    'scheduled': 'warning',
    'checking': 'info',
    'preparing': 'active',
}


redis_pool = redis.ConnectionPool(
    host=conf.redis_host,
    port=conf.redis_port,
    db=conf.redis_db
)


def get_pipeline():
    from jaci.workers import LocalBuilder
    return LocalBuilder(JSONRedisBackend)


def slugify(string):
    return re.sub(r'\W+', '', string)


def serialize_value(value):
    if isinstance(value, uuid.UUID):
        result = str(value)
    elif isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        result = str(value)
    elif hasattr(value, 'to_dict'):
        result = value.to_dict()
    else:
        result = value

    return result


def model_to_dict(instance, extra={}):
    data = {}
    for key, value in instance.items():
        data[key] = serialize_value(value)
    if isinstance(extra, dict):
        data.update(extra)
    else:
        msg = (
            "jaci.models.model_to_dict's 2nd "
            "argument `extra` must be a dict,"
            " got a {0} instead"
        )
        raise TypeError(msg.format(type(extra)))

    return data


class Builder(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    name = columns.Text(required=True)
    git_uri = columns.Text(index=True)
    shell_script = columns.Text(required=True)
    id_rsa_private = columns.Text()
    id_rsa_public = columns.Text()
    status = columns.Text(default='ready')
    branch = columns.Text(default='master')
    branch = columns.Text(default='master')

    def trigger(self, user, branch=None, author_name=None, author_email=None):
        build = Build.create(
            id=uuid.uuid1(),
            date_created=datetime.datetime.utcnow(),
            builder_id=self.id,
            branch=branch or self.branch,
            author_name=author_name,
            author_email=author_email,
        )
        pipeline = get_pipeline()
        payload = self.to_dict()
        payload.pop('last_build')
        payload.update(build.to_dict())
        payload['user'] = user.to_dict()
        pipeline.input.put(payload)
        logger.info("Scheduling builder: %s %s", self.name, self.git_uri)
        return build

    def get_last_build(self):
        results = Build.objects.filter(builder_id=self.id)
        if not results:
            return None

        return results[0]

    def to_dict(self):
        last_build = self.get_last_build()
        serialized_build = None
        if last_build:
            serialized_build = last_build.to_dict()
        result = model_to_dict(self, {
            'slug': slugify(self.name).lower(),
            'css_status': STATUS_MAP.get(self.status, 'success'),
            'last_build': serialized_build,
        })
        # result.pop('id_rsa_private', None)
        # result.pop('id_rsa_public', None)
        return result


class JaciPreference(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    key = columns.Text(required=True)
    value = columns.Text(required=True)

    def to_dict(self):
        return model_to_dict(self)


class Build(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    builder_id = columns.TimeUUID(required=True, index=True)
    branch = columns.Text(required=True)
    stdout = columns.Text()
    stderr = columns.Text()
    author_name = columns.Text()
    author_email = columns.Text()
    commit = columns.Text()
    code = columns.Integer()
    status = columns.Text(default='ready')
    date_created = columns.DateTime()
    date_finished = columns.DateTime()

    @property
    def builder(self):
        return Builder.get(id=self.builder_id)

    def save(self):
        builder = Builder.objects.get(id=self.builder_id)
        builder.status = self.status
        builder.save()
        return super(Build, self).save()

    def to_dict(self):
        return model_to_dict(self, {
            'css_status': STATUS_MAP.get(self.status, 'warning'),
        })

    @classmethod
    def calculate_redis_key_for(Build, builder_id, action):
        return b'build:{0}:{1}'.format(builder_id, action)

    @classmethod
    def push_live_output(Build, build_id, stdout, stderr):
        stdout_key = Build.calculate_redis_key_for(build_id, 'stdout')
        stderr_key = Build.calculate_redis_key_for(build_id, 'stderr')

        cache = redis.Redis(connection_pool=redis_pool)
        pipe = cache.pipeline()
        pipe.append(stdout_key, stdout)
        pipe.append(stderr_key, stderr)
        return pipe.execute()


class User(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    github_access_token = columns.Text(index=True)
    name = columns.Text()
    email = columns.Text()
    jaci_token = columns.UUID(required=True, index=True)

    def to_dict(self):
        return model_to_dict(self)

    def get_github_metadata(self):
        headers = {
            'Authorization': 'token {0}'.format(self.github_access_token)
        }
        response = requests.get('https://api.github.com/user', headers=headers)
        metadata = response.json()
        logging.warning("GITHUB USER METADATA: %s", metadata)
        return metadata

    def reset_token(self):
        self.jaci_token = uuid.uuid4()
        self.save()

    @classmethod
    def from_jaci_token(cls, jaci_token):
        if not jaci_token:
            return

        users = User.objects.filter(jaci_token=jaci_token)
        if len(users) > 0:
            return users[0]
