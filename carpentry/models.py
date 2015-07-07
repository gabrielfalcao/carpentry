# -*- coding: utf-8 -*-
#
import re
import json
import redis
import uuid
import requests
import hashlib
import logging
import datetime
import traceback
# from dateutil.parser import parse as parse_datetime
from lineup import JSONRedisBackend

from cqlengine import columns
from cqlengine.models import Model
from carpentry.util import render_string, force_unicode, response_did_succeed
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
    'scheduled': 'info',
    'checking': 'info',
    'preparing': 'info',
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
    from carpentry.workers import RunBuilder
    return RunBuilder(JSONRedisBackend)


def slugify(string):
    return re.sub(r'\W+', '', string).lower()


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
    id_rsa_private = columns.Text(required=True)
    id_rsa_public = columns.Text(required=True)
    status = columns.Text(default='ready')
    branch = columns.Text(default='master')

    creator_user_id = columns.UUID()
    github_hook_data = columns.Text()
    git_clone_timeout_in_seconds = columns.Integer(default=conf.default_subprocess_timeout_in_seconds)
    build_timeout_in_seconds = columns.Integer(default=conf.default_subprocess_timeout_in_seconds)
    # docker_dependencies = columns.Map(columns.Text(), columns.Text())

    def get_fallback_github_access_token(self):
        creator = User.get(id=self.creator_user_id)
        return creator.github_access_token

    def delete_single_github_hook(self, hook_id, github_access_token=None):
        github_access_token = github_access_token or self.get_fallback_github_access_token()
        headers = {
            'Authorization': 'token {0}'.format(github_access_token)
        }

        url = render_string('https://api.github.com/repos/{{owner}}/{{name}}/hooks/{0}'.format(hook_id), self.github_repo_info)
        response = requests.delete(url, headers=headers)
        return response

    def cleanup_github_hooks(self, github_access_token=None):
        if not github_access_token:
            creator = User.get(id=self.creator_user_id)
            github_access_token = creator.github_access_token

        headers = {
            'Authorization': 'token {0}'.format(github_access_token)
        }
        url = render_string('https://api.github.com/repos/{owner}/{name}/hooks', self.github_repo_info)

        response = requests.get(url, headers=headers)
        all_hooks = response.json()
        base_url = conf.get_full_url('')
        logger.info("%s hooks found for repo %s", len(all_hooks), self.github_repo_info)
        logger.info("trying to match them with the address: %s", base_url)
        if response.status_code > 300:
            logger.warning("github returned %s on %s:%s", response.status_code, url, response.text)
            return

        for hook in all_hooks:
            hook_config = hook.get('config', {})
            if not isinstance(hook_config, dict):
                logger.error("Hook config is a %s %s", type(hook_config), hook_config)
                hook_config = {}

            hook_url = hook_config.get('url', None)
            hook_id = hook['id']

            if not hook_url:
                logger.info("could not find a url in the config of the hook %s", hook)
                continue

            if hook_url.startswith(base_url):
                logger.info("removing hook %s from repo %s", hook_config, self.github_repo_info)
                self.delete_single_github_hook(
                    hook_id,
                    github_access_token
                )

    @classmethod
    def determine_github_repo_from_git_uri(self, git_uri):
        found = GITHUB_URI_REGEX.search(git_uri)
        if found:
            return found.groupdict()

        return {}

    @property
    def github_repo_info(self):
        return Builder.determine_github_repo_from_git_uri(self.git_uri)

    def determine_github_hook_url(self):
        path = '/api/hooks/{0}'.format(self.id)
        return conf.get_full_url(path)

    def set_github_hook(self, github_access_token):
        if self.github_hook_data:
            logging.warning('github hook already set for %s', self.name)
            return json.loads(self.github_hook_data)

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
        url = render_string('https://api.github.com/repos/{owner}/{name}/hooks', self.github_repo_info)
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
            'github_hook_url': self.determine_github_hook_url()
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
    commit_message = columns.Text()
    code = columns.Integer()
    status = columns.Text(default='ready')
    date_created = columns.DateTime()
    date_finished = columns.DateTime()
    github_status_data = columns.Text()
    github_webhook_data = columns.Text()
    docker_status = columns.Text()

    @property
    def author_gravatar_url(self):
        email_md5 = hashlib.md5(self.author_email or '').hexdigest()
        gravatar_url = 'https://s.gravatar.com/avatar/{0}'.format(
            email_md5,
        )
        return gravatar_url

    @property
    def url(self):
        path = render_string('/#/builder/{builder_id}/build/{id}', model_to_dict(self))
        return conf.get_full_url(path)

    @property
    def github_repo_info(self):
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
        url = render_string(template_url, self.github_repo_info)

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

    def append_to_stdout(self, string):
        if not isinstance(self.stdout, basestring):
            self.stdout = ''

        self.stdout += force_unicode(string)
        self.save()

    def set_status(self, status, description=None, github_access_token=None):
        self.status = status
        self.save()

        if not github_access_token:
            msg = "[github] {0} skipping set github build status to {1}"
            logger.info(msg.format(self, status))
            return

        github_status = GITHUB_STATUS_MAP.get(status, None)
        if github_status:
            self.set_github_status(github_access_token, github_status, description)

    def save(self):
        builder = Builder.objects.get(id=self.builder_id)
        last_builders_build = builder.get_last_build()

        if last_builders_build and last_builders_build.id == self.id:
            builder.status = self.status
            builder.save()

        return super(Build, self).save()

    def to_dict(self):
        result = model_to_dict(self, {
            'github_repo_info': self.github_repo_info,
            'css_status': STATUS_MAP.get(self.status, 'warning'),
            'author_gravatar_url': self.author_gravatar_url
        })
        docker_status = result.pop('docker_status', None) or '{}'
        try:
            deserialized_docker_status = json.loads(docker_status)
        except ValueError:
            deserialized_docker_status = {}

        result['docker_status'] = deserialized_docker_status
        return result

    def register_docker_status(self, line):
        self.stdout = self.stdout or b''
        try:
            json.loads(line)
            self.docker_status = force_unicode(line)
        except ValueError:
            self.stdout += force_unicode(line)
        except Exception as e:
            self.stdout += force_unicode(line)
            error = traceback.format_exc(e)
            self.stdout += force_unicode(error)

        self.save()


class User(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    github_access_token = columns.Text(index=True)
    name = columns.Text()
    email = columns.Text()
    carpentry_token = columns.UUID(required=True, index=True)
    github_metadata = columns.Text()

    def to_dict(self):
        return model_to_dict(self, extra={
            'github': self.get_github_metadata()
        })

    def get_github_metadata(self):
        if self.github_metadata:
            return json.loads(self.github_metadata)

        headers = {
            'Authorization': 'token {0}'.format(self.github_access_token)
        }
        response = requests.get('https://api.github.com/user', headers=headers)
        metadata = response.json()
        self.github_metadata = response.text
        self.save()
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

    def prepare_github_request_headers(self):
        headers = {
            'Authorization': 'token {0}'.format(self.github_access_token)
        }
        return headers

    def retrieve_organization_repos(self, name):
        headers = self.prepare_github_request_headers()
        url = 'https://api.github.com/orgs/{0}/repos'.format(name)
        response = requests.get(url, headers=headers)
        if not response_did_succeed(response):
            logger.info('[{0} repos] failed to retrieve {1}'.format(name, url))
            return []

        metadata = response.json()
        return metadata

    def retrieve_user_repos(self):
        headers = self.prepare_github_request_headers()
        url = 'https://api.github.com/user/repos'
        response = requests.get(url, headers=headers)
        if not response_did_succeed(response):
            logger.info('[user repos] failed to retrieve {0}'.format(url))
            return []

        metadata = response.json()
        return metadata

    def retrieve_and_cache_github_repositories(self):
        personal_repos = self.retrieve_user_repos()
        organization_repos = []
        for organization_name in conf.allowed_github_organizations:
            repos = self.retrieve_organization_repos(organization_name)
            organization_repos.extend(repos)

        all_repos = organization_repos + personal_repos
        GithubRepository.store_many_from_list(all_repos)
        return all_repos

    def get_github_organizations(self):
        github = self.get_github_metadata()
        organizations = github.get('organizations', None)
        if organizations:
            return organizations

        headers = {
            'Authorization': 'token {0}'.format(self.github_access_token)
        }
        url = render_string('https://api.github.com/user/orgs', github)
        response = requests.get(url, headers=headers)
        organizations = response.json()
        github['organizations'] = organizations
        self.github_metadata = json.dumps(github)
        self.save()
        return organizations


class GithubRepository(Model):
    """holds an individual repo coming as json from the github api
    response, the `name`, `owner` and `git_uri` are stored as fields
    of this model, and the full `response_data` is also available as a
    raw json value
    """
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    name = columns.Text(required=True)
    owner = columns.Text(required=True)
    git_uri = columns.Text(required=True, index=True)
    response_data = columns.Text(required=True)

    @classmethod
    def store_many_from_list(cls, items):
        for item in items:
            yield cls.store_one_from_dict(item)

    @classmethod
    def store_one_from_dict(cls, item):
        name = item['name']
        git_uri = item['git_uri']
        owner_info = item['owner']
        owner = owner_info['login']
        GithubOrganization.store_one_from_dict(owner_info)
        response_data = json.dumps(item)

        model = cls(
            id=uuid.uuid4(),
            name=name,
            git_uri=git_uri,
            owner=owner,
            response_data=response_data
        )
        model.save()
        return model


class GithubOrganization(Model):
    id = columns.TimeUUID(primary_key=True, partition_key=True)
    login = columns.Text(required=True)
    github_id = columns.Integer()
    avatar_url = columns.Text()
    url = columns.Text()
    html_url = columns.Text()
    response_data = columns.Text()

    @classmethod
    def store_one_from_dict(cls, item):
        login = item['login']
        github_id = item['id']
        avatar_url = item['avatar_url']
        url = item['url']
        html_url = item['html_url']
        response_data = json.dumps(item)

        model = cls(
            id=uuid.uuid4(),
            login=login,
            github_id=github_id,
            avatar_url=avatar_url,
            url=url,
            html_url=html_url,
            response_data=response_data
        )
        model.save()
        return model

    def to_dict(self):
        return model_to_dict(self)
