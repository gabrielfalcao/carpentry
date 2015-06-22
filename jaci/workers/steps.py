#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import os
import re
import json
import io
import requests
import shutil
import codecs
import yaml
from jaci import conf
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT, check_output, CalledProcessError
from lineup import Step
from jaci.util import calculate_redis_key, render_string
from jaci.models import Build
# import unicodedata


AUTHOR_REGEX = re.compile(
    r'Author: (?P<name>[^<]+\s*)[<](?P<email>[^>]+)[>]')

COMMIT_REGEX = re.compile(
    r'commit\s*(?P<commit>\w+)', re.I)


def run_command(command, chdir, bufsize=64):
    return Popen(command, stdout=PIPE, stderr=STDOUT, shell=True, cwd=chdir)


def force_unicode(string):
    if not isinstance(string, unicode):
        return unicode(string, errors='ignore')

    return string


def stream_output(step, process, redis_stdout_key):
    stdout = []

    for out in iter(lambda: process.stdout.read(1), ''):
        out = force_unicode(out)
        step.backend.redis.append(redis_stdout_key, out)
        stdout.append(out)

    exit_code = process.wait()
    try:
        return ''.join(stdout), exit_code
    except UnicodeDecodeError:
        return ''.encode('utf-8').join(stdout), exit_code


def get_build_from_instructions(instructions):
    return Build.objects.get(id=instructions['id'])


def set_build_status(instructions, status):
    build = get_build_from_instructions(instructions)
    build.status = status
    build.save()


class PrepareSSHKey(Step):
    def write_file(self, path, filename, contents, mode=0755):
        if not os.path.exists(path):
            os.makedirs(path)

        destination = os.path.join(path, filename)
        with io.open(destination, 'wb') as fd:
            fd.write(contents)

        os.chmod(destination, mode)

    def consume(self, instructions):
        set_build_status(instructions, 'running')
        slug = instructions['slug']
        workdir = conf.build_node.join('builds/{0}'.format(slug))

        ssh_dir = conf.workdir_node.join('ssh-keys/{0}'.format(slug))

        private_key = instructions['id_rsa_private']
        public_key = instructions['id_rsa_public']

        id_rsa_private_key_path = render_string('{slug}-id_rsa', instructions)
        id_rsa_public_key_path = render_string('{slug}-id_rsa.pub', instructions)
        instructions['id_rsa_private_key_path'] = os.path.join(ssh_dir, id_rsa_private_key_path)
        instructions['id_rsa_public_key_path'] = os.path.join(ssh_dir, id_rsa_public_key_path)

        self.write_file(ssh_dir, id_rsa_private_key_path, private_key, mode=0600)
        self.write_file(ssh_dir, id_rsa_public_key_path, public_key, mode=0644)

        redis_stdout_key, redis_stderr_key = calculate_redis_key(instructions)
        instructions['redis_stdout_key'] = redis_stdout_key
        instructions['redis_stderr_key'] = redis_stderr_key

        instructions['ssh_dir'] = ssh_dir
        instructions['workdir'] = workdir
        try:
            instructions['ssh_add'] = check_output(render_string('ssh-add {id_rsa_private_key_path}', instructions), shell=True)
        except CalledProcessError:
            pass
        self.produce(instructions)


class PushKeyToGithub(Step):
    REGEX = re.compile(r'(?P<owner>[^/]+)/(?P<repo>[^/]+)(.git)?')

    def parse_github_repo(self, instructions):
        git_uri = instructions['git_uri']
        found = self.REGEX.search(git_uri)
        if found:
            data = found.groupdict()
            return data['owner'], data['repo']

    def consume(self, instructions):
        github_access_token = instructions['user']['github_access_token']

        headers = {
            'Authorization': 'token {0}'.format(github_access_token)
        }
        owner_and_repo = self.parse_github_repo(instructions)
        if not owner_and_repo:
            self.log('INVALID GITHUB REPO, not pushing ssh keys as deploy keys')
            return self.produce(instructions)

        owner, repo = owner_and_repo
        url = 'https://api.github.com/repos/{0}/{1}/keys'.format(owner, repo)
        payload = json.dumps({
            "title": "jaci {0}".format(instructions['name']),
            "key": instructions['id_rsa_private'],
            "read_only": True
        })
        response = requests.post(url, data=payload, headers=headers)
        instructions['github_deploy_key'] = response.json()
        self.produce(instructions)


class LocalRetrieve(Step):
    def consume(self, instructions):
        set_build_status(instructions, 'retrieving')

        slug = instructions['slug']
        workdir = conf.workdir_node.join(slug)
        build_dir = conf.build_node.join(slug)

        redis_stdout_key, redis_stderr_key = calculate_redis_key(instructions)
        instructions['redis_stdout_key'] = redis_stdout_key
        instructions['redis_stderr_key'] = redis_stderr_key
        instructions['workdir'] = workdir
        instructions['build_dir'] = build_dir

        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        # else:
        git = render_string('/usr/bin/env git clone -b {branch} {git_uri} ' + build_dir, instructions)
        chdir = conf.workdir_node.path

        # TODO: sanitize the git url before using it, avoid shell injection :O
        process = run_command(git, chdir=chdir)

        stdout, exit_code = stream_output(self, process, redis_stdout_key)
        instructions['git'] = {
            'stdout': stdout,
            'exit_code': exit_code,
        }
        b = Build.objects.get(id=instructions['id'])
        if int(exit_code) != 0:
            self.log('Git clone failed {0}'.format(stdout))
            b.status = 'failed'
            b.save()
            raise RuntimeError('Failed to git clone')

        if b.stdout is None:
            b.stdout = u''

        b.stdout += force_unicode(stdout)
        b.code = int(exit_code)
        b.save()

        git_show = '/usr/bin/env git show HEAD'
        git_show_stdout = check_output(git_show, cwd=chdir, shell=True)

        author = AUTHOR_REGEX.search(git_show_stdout)
        commit = COMMIT_REGEX.search(git_show_stdout)
        meta = {}

        if commit:
            b.commit = commit.group('commit')
            meta.update(commit.groupdict())

        if author:
            b.author_name = author.group('name')
            b.author_email = author.group('email')
            meta.update(author.groupdict())

        b.save()
        self.log("meta: %s", meta)
        instructions['git'].update(meta)
        self.produce(instructions)


class CheckAndLoadBuildFile(Step):
    def consume(self, instructions):
        set_build_status(instructions, 'checking')

        build_dir = instructions['build_dir']
        yml_path = os.path.join(build_dir, '.jaci.yml')

        if not os.path.exists(yml_path):
            instructions['build'] = {'shell': instructions['shell_script']}
            return self.produce(instructions)

        with codecs.open(yml_path, 'r', 'utf-8') as fd:
            raw_yml = fd.read()

        self.log("Successfully loaded {0}".format(yml_path))
        build = yaml.load(raw_yml)
        instructions['build'] = build

        self.produce(instructions)


class PrepareShellScript(Step):
    def write_script_to_fd(self, fd, template, instructions):
        rendered = render_string(template, instructions)
        self.log(rendered.strip())
        fd.write(rendered)
        fd.write('\n')

    def consume(self, instructions):
        set_build_status(instructions, 'preparing')
        build_dir = instructions['build_dir']
        shell_script_path = os.path.join(build_dir, render_string('.{slug}.shell.sh', instructions))
        instructions['shell_script_path'] = shell_script_path

        self.log(render_string('writing {shell_script_path}', instructions))

        with io.open(shell_script_path, 'wb') as fd:
            self.write_script_to_fd(fd, "#!/bin/bash", instructions)
            self.write_script_to_fd(fd, "set -e", instructions)
            self.write_script_to_fd(fd, instructions['build']['shell'], instructions)

        os.chmod(shell_script_path, 0755)

        self.produce(instructions)


class LocalBuild(Step):
    def consume(self, instructions):
        set_build_status(instructions, 'running')
        cmd = render_string('bash {shell_script_path}', instructions)

        self.log(render_string("running: bash {shell_script_path}", instructions))
        self.log(render_string("cwd: {build_dir}", instructions))

        process = run_command(cmd, chdir=instructions['build_dir'])
        redis_stdout_key, redis_stderr_key = calculate_redis_key(instructions)

        stdout, exit_code = stream_output(self, process, redis_stdout_key)
        instructions['shell'] = {
            'stdout': stdout,
            'exit_code': exit_code,
        }

        b = Build.objects.get(id=instructions['id'])
        if b.stdout is None:
            b.stdout = ''

        b.stdout += force_unicode(stdout)
        b.code = int(exit_code)
        b.date_finished = datetime.utcnow()
        b.save()

        if b.code == 0:
            status = 'succeeded'
        else:
            status = 'failed'

        instructions['status'] = status
        self.log(render_string("build of {name} {status}", instructions))

        set_build_status(instructions, status)
        self.produce(instructions)
