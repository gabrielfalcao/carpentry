# -*- coding: utf-8 -*-
#
import re
import redis
import uuid
# import bcrypt
# import logging
# from dateutil.parser import parse as parse_datetime
from datetime import datetime
from cqlengine import columns
from cqlengine import connection
from cqlengine.models import Model
from jaci import conf


redis_pool = redis.ConnectionPool(
    host=conf.redis_host,
    port=conf.redis_port,
    db=conf.redis_db
)

connection.setup(conf.cassandra_hosts, default_keyspace='jaci')


def slugify(string):
    return re.sub(r'\W+', '', string)

BUILD_STATUSES = [
    'ready',      # no builds scheduled
    'scheduled',  # scheduled but not yet running
    'running',    # running
    'succeeded',  # finished with success, subprocess returned status 0
    'failed',     # finished with an error, subprocess returned status != 0
]


class Builder(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    name = columns.Text(required=True)
    git_url = columns.Text(index=True)
    shell_script = columns.Text(required=True)
    id_rsa_private = columns.Text()
    id_rsa_public = columns.Text()
    status = columns.Text(default='ready')
    branch = columns.Text(default='master')

    def trigger(self, branch):
        return Build.create(
            id=uuid.uuid1(),
            date_created=datetime.utcnow(),
            builder_id=self.id,
            branch=branch or self.branch
        )

    def to_dict(self):
        return dict(self.items())


class JaciPreference(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    key = columns.Text(required=True)
    value = columns.Text(required=True)

    def to_dict(self):
        return dict(self.items())


class Build(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    builder_id = columns.TimeUUID(required=True, partition_key=True)
    branch = columns.Text(required=True)
    stdout = columns.Text()
    stderr = columns.Text()
    code = columns.Integer()
    status = columns.Text(default='scheduled')
    date_created = columns.DateTime()
    date_finished = columns.DateTime()

    def save(self):
        builder = Builder.objects.get(id=self.builder_id)
        builder.status = self.status
        builder.save()
        return super(Build, self).save()

    def to_dict(self):
        return dict(self.items())

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
