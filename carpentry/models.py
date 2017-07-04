# -*- coding: utf-8 -*-
#
import re
import json

import uuid
import requests
import hashlib
import logging
import datetime

# from dateutil.parser import parse as parse_datetime
from lineup import JSONRedisBackend

from repocket import attributes
from repocket import ActiveRecord
from repocket import configure
from repocket.util import is_null
from carpentry.util import render_string, force_unicode, response_did_succeed
from carpentry import conf

logger = logging.getLogger('carpentry.models')

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


GITHUB_URI_REGEX = re.compile(
    r'github.com[:/](?P<owner>[\w_-]+)[/](?P<name>[\w_-]+)([.]git)?')


redis_pool = configure.connection_pool(
    hostname=conf.redis_host,
    port=conf.redis_port,
    db=conf.redis_db
)


def get_pipeline():
    from carpentry.workers import RunBuilder
    return RunBuilder(JSONRedisBackend)


def slugify(string):
    return re.sub(r'\W+', '', string).lower()


def prepare_value_for_serialization(value):
    if isinstance(value, uuid.UUID):
        result = str(value)
    elif isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        result = str(value)
    elif hasattr(value, 'to_dict'):
        result = value.to_dict(simple=True)
    else:
        result = value

    return result


def model_to_dictionary(instance, extra=None):
    if extra is None:
        extra = {}
    data = {}
    for key, value in instance.to_dict(simple=True).items():
        data[key] = prepare_value_for_serialization(value)

    data.update(extra)
    return data


class CarpentryBaseActiveRecord(ActiveRecord):

    def prepare_github_request_headers(self, github_access_token=None):
        github_access_token = github_access_token or getattr(
            self, 'github_access_token', None)
        headers = {
            'Authorization': 'token {0}'.format(github_access_token)
        }
        return headers


class CarpentryPreference(CarpentryBaseActiveRecord):
    id = attributes.AutoUUID()
    key = attributes.Unicode()
    value = attributes.Unicode()


class User(CarpentryBaseActiveRecord):
    id = attributes.AutoUUID()
    github_access_token = attributes.Unicode()
    name = attributes.Unicode()
    email = attributes.Unicode()
    carpentry_token = attributes.UUID()
    github_metadata = attributes.JSON()

    @property
    def organization_names(self):
        self._organization_names = getattr(self, '_organization_names', None)
        if not self._organization_names:
            self._organization_names = [o['login'] for o in self.organizations]

        return self._organization_names

    @property
    def organizations(self):
        return self.retrieve_github_organizations()

    def to_dictionary(self):
        return model_to_dictionary(self, extra={
            'github': self.get_github_metadata(),
        })

    def get_github_metadata(self):
        headers = self.prepare_github_request_headers()
        response = requests.get('https://api.github.com/user', headers=headers)
        if response.status_code == 200:
            self.github_metadata = response.json()
            self.save()

        return self.github_metadata

    def reset_token(self):
        self.carpentry_token = uuid.uuid4()
        self.save()

    @classmethod
    def from_carpentry_token(cls, carpentry_token):
        if not carpentry_token:
            return

        try:
            token = uuid.UUID(bytes(carpentry_token))
        except TypeError:
            logger.exception("Failed to query user by the carpentry_token: %s", carpentry_token)

        users = cls.objects.filter(carpentry_token=token)
        if len(users) > 0:
            return users[0]

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

    def retrieve_github_organizations(self):
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
        self.github_metadata = github
        self.save()
        return organizations


class GithubRepository(CarpentryBaseActiveRecord):

    """holds an individual repo coming as json from the github api
    response, the `name`, `owner` and `git_uri` are stored as fields
    of this model, and the full `response_data` is also available as a
    raw json value
    """
    id = attributes.AutoUUID()
    name = attributes.Unicode()
    owner = attributes.Unicode()
    git_uri = attributes.Unicode()
    response_data = attributes.Unicode()

    @classmethod
    def store_many_from_list(cls, items):
        results = []
        for item in items:
            r = cls.store_one_from_dict(item)
            results.append(r)

        return results

    @classmethod
    def store_one_from_dict(cls, item):
        name = item['name']
        git_uri = item['ssh_url']
        owner_info = item['owner']
        owner = owner_info['login']
        GithubOrganization.store_one_from_dict(owner_info)
        response_data = json.dumps(item)

        model = cls(
            id=uuid.uuid1(),
            name=name,
            git_uri=git_uri,
            owner=owner,
            response_data=response_data
        )
        model.save()
        return model


class GithubOrganization(CarpentryBaseActiveRecord):
    id = attributes.AutoUUID()
    login = attributes.Unicode()
    github_id = attributes.Integer()
    avatar_url = attributes.Unicode()
    url = attributes.Unicode()
    html_url = attributes.Unicode()
    response_data = attributes.Unicode()

    @classmethod
    def store_one_from_dict(cls, item):
        login = item['login']
        github_id = item['id']
        avatar_url = item['avatar_url']
        url = item['url']
        html_url = item['html_url']
        response_data = json.dumps(item)

        model = cls(
            id=uuid.uuid1(),
            login=login,
            github_id=github_id,
            avatar_url=avatar_url,
            url=url,
            html_url=html_url,
            response_data=response_data
        )
        model.save()
        return model


class Builder(CarpentryBaseActiveRecord):
    id = attributes.AutoUUID()
    name = attributes.Unicode()
    git_uri = attributes.Bytes()
    shell_script = attributes.Unicode()
    json_instructions = attributes.Unicode()
    id_rsa_private = attributes.Unicode()
    id_rsa_public = attributes.Unicode()
    status = attributes.Unicode()
    branch = attributes.Unicode()

    creator = attributes.Pointer(User)
    github_hook_data = attributes.Unicode()
    git_clone_timeout_in_seconds = attributes.Integer(
        default=conf.default_subprocess_timeout_in_seconds)
    build_timeout_in_seconds = attributes.Integer(
        default=conf.default_subprocess_timeout_in_seconds)

    def get_fallback_github_access_token(self):
        return self.creator.github_access_token

    def get_all_builds(self):
        return Build.objects.filter(builder=self)

    @property
    def github_access_token(self):
        return self.get_fallback_github_access_token()

    def delete_single_github_hook(self, hook_id, github_access_token):
        headers = self.prepare_github_request_headers(github_access_token)
        url = render_string(
            'https://api.github.com/repos/{{owner}}/{{name}}/hooks/{0}'.format(hook_id), self.github_repo_info)
        response = requests.delete(url, headers=headers)
        return response

    def list_github_hooks(self, github_access_token=None):
        headers = self.prepare_github_request_headers(
            github_access_token
        )

        url = render_string(
            'https://api.github.com/repos/{owner}/{name}/hooks',
            self.github_repo_info
        )
        response = requests.get(url, headers=headers)

        try:
            all_hooks = response.json()
        except ValueError:
            msg = '[{0}] github failed to list hooks:\n{1}\n'.format(
                url,
                response.text
            )
            logger.warning(msg)
            all_hooks = []

        return all_hooks

    def cleanup_github_hooks(self, github_access_token=None):
        all_hooks = self.list_github_hooks(github_access_token)
        base_url = conf.get_full_url('')
        logger.info(
            "%s hooks found for repo %s",
            len(all_hooks),
            self.github_repo_info
        )

        for hook in all_hooks:
            if 'config' not in hook:
                logger.warning("ignoring empty hook %s", hook)
                continue

            hook_config = hook['config']
            hook_url = hook_config.get('url', None)
            hook_id = hook['id']

            if not hook_url:
                continue

            if hook_url.startswith(base_url):
                logger.info(
                    "removing hook %s from repo %s",
                    hook_config,
                    self.github_repo_info
                )
                self.delete_single_github_hook(
                    hook_id,
                    github_access_token
                )

    @classmethod
    def determine_github_repo_from_git_uri(self, git_uri):
        found = not is_null(git_uri) and GITHUB_URI_REGEX.search(git_uri)
        if found:
            return found.groupdict()

        return {}

    @property
    def github_repo_info(self):
        return Builder.determine_github_repo_from_git_uri(
            self.git_uri
        )

    def determine_github_hook_url(self):
        path = '/api/hooks/{0}'.format(self.id)
        return conf.get_full_url(path)

    def set_github_hook(self, github_access_token):
        if self.github_hook_data:
            logging.warning(
                'github hook already set for %s',
                self.name
            )
            return json.loads(self.github_hook_data)

        headers = self.prepare_github_request_headers(
            github_access_token
        )

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
        url = render_string(
            'https://api.github.com/repos/{owner}/{name}/hooks',
            self.github_repo_info
        )
        response = requests.post(
            url,
            data=request_payload,
            headers=headers
        )
        self.github_hook_data = response.text
        self.save()
        logging.warning(
            "when setting github hook %s %s",
            url,
            response
        )
        return response.json()

    def trigger(self, user, branch=None, commit=None,
                author_name=None, author_email=None,
                github_webhook_data=None):

        build = Build.create(
            id=uuid.uuid1(),
            date_created=datetime.datetime.utcnow(),
            builder=self,
            branch=branch or self.branch or 'master',
            author_name=author_name,
            author_email=author_email,
            git_uri=self.git_uri,
            github_webhook_data=github_webhook_data,
            commit=commit,
            status='ready',
        )
        pipeline = get_pipeline()
        payload = self.to_dictionary()
        payload['id_rsa_public'] = self.id_rsa_public
        payload['id_rsa_private'] = self.id_rsa_private
        payload.pop('last_build', None)
        payload.update(build.to_dictionary())
        payload['user'] = user.to_dictionary()

        pipeline.input.put(payload)
        logger.info("Scheduling builder: %s %s", self.name, self.git_uri)
        return build

    def clear_builds(self):
        deleted_builds = []
        for build in Build.objects.filter(builder=self):
            deleted_builds.append(build)
            build.delete()

        return deleted_builds

    def get_last_build(self):
        results = Build.objects.filter(builder=self)
        if not results:
            return None

        return results[0]

    def to_dictionary(self):
        last_build = self.get_last_build()

        serialized_build = None
        if last_build:
            serialized_build = last_build.to_dictionary()

        result = model_to_dictionary(self, {
            'slug': slugify(self.name).lower(),
            'css_status': STATUS_MAP.get(self.status, 'success'),
            'last_build': serialized_build,
            'github_hook_url': self.determine_github_hook_url()
        })
        result.pop('id_rsa_private', None)
        result.pop('id_rsa_public', None)
        return result


class Build(CarpentryBaseActiveRecord):
    id = attributes.AutoUUID()
    builder = attributes.Pointer(Builder)
    git_uri = attributes.Unicode()
    branch = attributes.Unicode()
    stdout = attributes.ByteStream()
    stderr = attributes.ByteStream()
    author_name = attributes.Unicode()
    author_email = attributes.Unicode()
    commit = attributes.Unicode()
    commit_message = attributes.Unicode()
    code = attributes.Integer()
    status = attributes.Unicode()
    date_created = attributes.DateTime()
    date_finished = attributes.DateTime()
    github_status_data = attributes.Unicode()
    github_webhook_data = attributes.Unicode()
    docker_status = attributes.Unicode()

    @property
    def author_gravatar_url(self):
        email_md5 = hashlib.md5(self.author_email or '').hexdigest()
        gravatar_url = 'https://s.gravatar.com/avatar/{0}'.format(
            email_md5,
        )
        return gravatar_url

    @property
    def url(self):
        if not self.builder:
            logger.error("Could not calculate build url because its parent builder is None: %s", self.to_dict(simple=True))
            return None
        path = render_string(
            '/#/builder/{builder[id]}/build/{id}', model_to_dictionary(self))
        return conf.get_full_url(path)

    @property
    def github_repo_info(self):
        return Builder.determine_github_repo_from_git_uri(self.git_uri)

    @property
    def github_status_info(self):
        try:
            return json.loads(self.github_status_data)
        except (TypeError, ValueError):
            # either github_status_data is None or is not a valid json
            return {}

    def set_github_status(self, github_access_token, status, description):
        # options: pending, success, error, or failure
        options = ['pending', 'success', 'error', 'failure']
        if status not in options:
            raise ValueError('Build.set_github_status got an invalid status: {0} our of the options {1}'.format(
                status, '. '.join(options)
            ))

        headers = self.prepare_github_request_headers(
            github_access_token)
        template_url = 'https://api.github.com/repos/{{owner}}/{{name}}/statuses/{0}'.format(
            self.commit)
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

    def append_to_stdout(self, string):
        value = force_unicode(string)
        self.append_to_bytestream('stdout', value)
        msg = '{0} {1}'.format(self.github_repo_info, value).strip()
        logger.info(msg)

    def set_status(self, status, description=None, github_access_token=None):
        self.status = status
        self.save()

        if not github_access_token:
            msg = "[github] {0} skipping set github build status to {1}"
            logger.info(msg.format(self, status))
            return

        github_status = GITHUB_STATUS_MAP.get(status, 'pending')
        self.set_github_status(
            github_access_token,
            github_status,
            description
        )

    def save(self):
        builder = self.builder
        builder.status = self.status
        builder.save()
        return super(Build, self).save()

    def to_dictionary(self):
        result = model_to_dictionary(self, {
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
        try:
            json.loads(line)
            self.docker_status = line
            self.save()
            msg = 'registered docker status: {0}'.format(line)
            logger.info(msg)
        except ValueError:
            self.append_to_stdout(line)
