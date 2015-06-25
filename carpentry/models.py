# -*- coding: utf-8 -*-
#
import re
import json
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
from carpentry.util import render_string
from carpentry import conf

logger = logging.getLogger('carpentry')

BUILD_STATUSES = [
    'ready',      # no builds scheduled
    'scheduled',  # scheduled but not yet running
    'retrieving',    # git clone
    'checking',    # looking for .carpentry.yml
    'preparing',    # preparing shell script
    'running',    # running
    'succeeded',  # finished with success, subprocess returned status 0
    'failed',     # finished with an error, subprocess returned status != 0
]


STATUS_MAP = {
    'ready': 'success',
    'succeeded': 'success',
    'failed': 'danger',
    'retrieving': 'info',
    'running': 'warning',
    'scheduled': 'warning',
    'checking': 'info',
    'preparing': 'active',
}

GITHUB_STATUS_MAP = {
    'running': 'pending',
    'failed': 'failure',
    'succeeded': 'success',
}


GITHUB_URI_REGEX = re.compile(r'github.com[:/](?P<owner>[\w_-]+)[/](?P<name>[\w_-]+)([.]git)?')

redis_pool = redis.ConnectionPool(
    host=conf.redis_host,
    port=conf.redis_port,
    db=conf.redis_db
)


def get_pipeline():
    from carpentry.workers import LocalBuilder
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
            "carpentry.models.model_to_dict's 2nd "
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
    creator_user_id = columns.UUID()
    github_hook_data = columns.Text()

    @classmethod
    def determine_github_repo_from_git_uri(self, git_uri):
        found = GITHUB_URI_REGEX.search('github.com:gabrielfalcao/sure')
        if found:
            return found.groupdict()

        return {}

    @property
    def github_info(self):
        return Builder.determine_github_repo_from_git_uri(self.git_uri)

    def determine_github_hook_url(self):
        path = '/api/hooks/{0}'.format(self.id)
        return conf.get_full_url(path)

    def set_github_hook(self, github_access_token):
        headers = {
            'Authorization': 'token {0}'.format(github_access_token)
        }
        request_payload = json.dumps({
            "name": "web",
            "active": True,
            "events": [
                "push",
                "pull_request"
            ],
            "config": {
                "url": self.determine_github_hook_url(),
                "content_type": "json"
            }
        })
        url = render_string('https://api.github.com/repos/{owner}/{name}/hooks', self.github_info)
        response = requests.post(url, data=request_payload, headers=headers)
        self.github_hook_data = response.text
        self.save()
        logging.warning("when setting github hook %s %s", url, response)
        return response.json()

    @property
    def github_hook_info(self):
        if not self.github_hook_data:
            msg = "Attempted to retrieve github_hook_info for builder {0}"
            logger.warning(msg.format(self.id))
            return {}

        return json.loads(self.github_hook_data)

    def trigger(self, user, branch=None, commit=None, author_name=None, author_email=None, github_webhook_data=None):
        build = Build.create(
            id=uuid.uuid1(),
            date_created=datetime.datetime.utcnow(),
            builder_id=self.id,
            branch=branch or self.branch or 'master',
            author_name=author_name,
            author_email=author_email,
            git_uri=self.git_uri,
            github_webhook_data=github_webhook_data,
            commit=commit
        )
        pipeline = get_pipeline()
        payload = self.to_dict()
        payload.pop('last_build')
        payload.update(build.to_dict())
        payload['user'] = user.to_dict()

        pipeline.input.put(payload)
        logger.info("Scheduling builder: %s %s", self.name, self.git_uri)
        return build

    def clear_builds(self):
        deleted_builds = []
        for build in Build.objects.filter(builder_id=self.id):
            deleted_builds.append(build)
            build.delete()

        return deleted_builds

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


class CarpentryPreference(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    key = columns.Text(required=True)
    value = columns.Text(required=True)

    def to_dict(self):
        return model_to_dict(self)


class Build(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    builder_id = columns.TimeUUID(required=True, index=True)
    git_uri = columns.Text()
    branch = columns.Text(required=True)
    stdout = columns.Text()
    stderr = columns.Text()
    author_name = columns.Text()
    author_email = columns.Text(index=True)
    commit = columns.Text()
    code = columns.Integer()
    status = columns.Text(default='ready')
    date_created = columns.DateTime()
    date_finished = columns.DateTime()
    github_status_data = columns.Text()
    github_webhook_data = columns.Text()

    @property
    def url(self):
        path = render_string('/#/builder/{builder_id}/build/{id}', model_to_dict(self))
        return conf.get_full_url(path)

    @property
    def github_info(self):
        return Builder.determine_github_repo_from_git_uri(self.git_uri)

    @property
    def github_status_info(self):
        if not self.github_status_data:
            return {}

        return json.loads(self.github_status_data)

    def set_github_status(self, github_access_token, status, description):
        # options: pending, success, error, or failure
        options = ['pending', 'success', 'error', 'failure']
        if status not in options:
            raise ValueError('Build.set_github_status got an invalid status: {0} our of the options {1}'.format(
                status, '. '.join(options)
            ))

        headers = {
            'Authorization': 'token {0}'.format(github_access_token)
        }
        template_url = 'https://api.github.com/repos/{{owner}}/{{name}}/statuses/{0}'.format(self.commit)
        url = render_string(template_url, self.github_info)

        request_payload = json.dumps({
            "state": "success",
            "target_url": self.url,
            "description": description,
            "context": "continuous-integration/carpentry"
        })

        logger.info("setting github hook %s:\n%s", url, request_payload)
        response = requests.post(url, data=request_payload, headers=headers)
        self.github_status_data = response.text
        self.save()

        return response.json()

    @property
    def builder(self):
        return Builder.get(id=self.builder_id)

    def save(self):
        builder = Builder.objects.get(id=self.builder_id)
        last_builders_build = builder.get_last_build()

        if last_builders_build and last_builders_build.id == self.id:
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
    carpentry_token = columns.UUID(required=True, index=True)

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
        self.carpentry_token = uuid.uuid4()
        self.save()

    @classmethod
    def from_carpentry_token(cls, carpentry_token):
        if not carpentry_token:
            return

        users = User.objects.filter(carpentry_token=carpentry_token)
        if len(users) > 0:
            return users[0]
