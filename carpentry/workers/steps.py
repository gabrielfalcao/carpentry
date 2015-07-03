#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals

import os
import re
import json
import time
import logging
import traceback
import io
import requests
import shutil
import codecs
import yaml
from carpentry import conf
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT, check_output, CalledProcessError
from lineup import Step

from docker.utils import create_host_config

from carpentry.util import render_string, get_docker_client
from carpentry.models import Build
# import unicodedata


AUTHOR_REGEX = re.compile(
    r'Author: (?P<name>[^<]+\s*)[<](?P<email>[^>]+)[>]')

COMMIT_REGEX = re.compile(
    r'commit\s*(?P<commit>\w+)', re.I)

COMMIT_MESSAGE_REGEX = re.compile(
    r'Date:.*?\n\s*(?P<commit_message>.*?)\s*^diff --git', re.M | re.S)


def response_did_succeed(response):
    return int(response.status_code) in [
        200,
        201,
        202,
        204,
        205,
        206,
    ]


def run_command(command, chdir, environment={}):
    try:
        return Popen(command, stdout=PIPE, stderr=STDOUT, shell=True, cwd=chdir, env=environment)
    except Exception:
        logging.exception("Failed to run {0}".format(command))


def force_unicode(string):
    if not isinstance(string, unicode):
        return unicode(string, errors='ignore')

    return string


def stream_output(step, process, build, stdout_chunk_size=1024, timeout_in_seconds=None):
    if not build.stdout:
        build.stdout = ''

    stdout = []
    current_transfered_bytes = 0
    started_time = time.time()
    difference = time.time() - started_time

    timeout_in_seconds = int(timeout_in_seconds or conf.default_subprocess_timeout_in_seconds)

    while difference < timeout_in_seconds:
        difference = (time.time() - started_time)
        raw = process.stdout.readline()
        if not raw:
            break

        out = force_unicode(raw)
        current_transfered_bytes += len(out)
        build.stdout += out
        stdout.append(out)
        if current_transfered_bytes >= stdout_chunk_size:
            build.save()
            current_transfered_bytes = 0

    timed_out = difference > timeout_in_seconds
    if timed_out:
        out = "\nBuild timed out by {0} seconds".format(difference)
        build.stdout += out
        build.stderr += out

        process.terminate()
        exit_code = 420
    else:
        exit_code = process.wait()

    build.save()
    return ''.join(stdout), exit_code


def get_build_from_instructions(instructions):
    return Build.objects.get(id=instructions['id'])


def set_build_status(instructions, status, description=None):
    build = get_build_from_instructions(instructions)

    user = instructions.get('user', {})
    github_access_token = user.get('github_access_token', None)

    build.set_status(status, description=description, github_access_token=github_access_token)
    return build


class CarpentryPipelineStep(Step):
    def handle_exception(self, e, instructions):
        build = get_build_from_instructions(instructions)
        tb = traceback.format_exc(e)
        build.set_status('failed')
        build.append_to_stdout(tb)


class PrepareSSHKey(CarpentryPipelineStep):
    def write_file(self, path, filename, contents, mode=0755):
        destination = os.path.join(path, filename)

        destination_dir = os.path.split(destination)[0]
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        with io.open(destination, 'wb') as fd:
            fd.write(contents)
            fd.write('\n')

        os.chmod(destination, mode)

    def consume(self, instructions):
        b = get_build_from_instructions(instructions)
        b.append_to_stdout('preparing ssh key...\n')

        now = datetime.utcnow()

        set_build_status(instructions, 'running', 'carpentry build started at {0} UTC'.format(now.strftime('%Y/%m/%d %H:%M:%S')))
        slug = instructions['slug']

        ssh_dir = conf.ssh_keys_node.join(slug)

        private_key = instructions.get('id_rsa_private', None)
        public_key = instructions.get('id_rsa_public', None)

        id_rsa_private_key_path = render_string('{slug}-id_rsa', instructions)
        id_rsa_public_key_path = render_string('{slug}-id_rsa.pub', instructions)

        instructions['id_rsa_private_key_path'] = os.path.join(ssh_dir, id_rsa_private_key_path)
        instructions['id_rsa_public_key_path'] = os.path.join(ssh_dir, id_rsa_public_key_path)

        if not private_key:
            msg = render_string(
                'the builder {builder_id} does not have a private_key set',
                instructions
            )
            b.append_to_stdout(msg)
            raise RuntimeError(msg)

        if not public_key:
            msg = render_string(
                'the builder {builder_id} does not have a public_key set',
                instructions
            )
            b.append_to_stdout(msg)
            raise RuntimeError(msg)

        self.write_file(
            ssh_dir,
            id_rsa_private_key_path,
            private_key,
            mode=0600
        )
        self.write_file(
            ssh_dir,
            id_rsa_public_key_path,
            public_key,
            mode=0644
        )

        command = render_string(
            'ssh-add {id_rsa_private_key_path}',
            instructions
        )

        try:
            ssh_add_output = check_output(
                command,
                shell=True
            )
            b.append_to_stdout(command)
            b.append_to_stdout('\n')
            b.append_to_stdout(ssh_add_output)
            b.append_to_stdout('\n')

        except CalledProcessError as e:
            tb = traceback.format_exc(e)
            b.append_to_stdout(tb)

        self.produce(instructions)


class PushKeyToGithub(CarpentryPipelineStep):
    REGEX = re.compile(r'(?P<owner>[\w_-]+)/(?P<repo>[\w_-]+)([.]git)?$')

    def push_keys_into_api_and_get_response(self, title, owner, repo, key, access_token):
        headers = {
            'Authorization': 'token {0}'.format(access_token)
        }

        url = 'https://api.github.com/repos/{0}/{1}/keys'.format(owner, repo)
        payload = json.dumps({
            "title": title,
            "key": key,
            "read_only": True
        }, indent=2)

        self.log("Pushing deploy keys to github {0}".format(url))
        self.log("Pushing deploy keys to github {0}".format(payload))

        response = requests.post(url, data=payload, headers=headers)
        return response

    def dump_error_into_build_output(self, build, response):
        msg = "%s: failed to push deploy key %s"
        logging.error(msg, response.status_code, response.text)
        build.append_to_stdout('failed')
        build.append_to_stdout("\n--------------------\n")
        build.append_to_stdout("Failed to push deploy key\n")
        build.append_to_stdout("RESPONSE:\n\n")
        build.append_to_stdout(response.text)
        build.append_to_stdout("\n--------------------\n")

    def consume(self, instructions):
        github_repo_info = instructions.get('github_repo_info', {})
        build = get_build_from_instructions(instructions)
        if not github_repo_info:
            msg = render_string(
                '{name} declared an invalid github repo: {git_uri}, '
                'not pushing ssh keys as deploy keys',
                instructions
            )
            build.append_to_stdout(msg)
            self.log(msg)
            return

        build.append_to_stdout("pushing key to github...\n")
        user = instructions['user']

        # gathering data to form the payload
        title = render_string("carpentry {name}", instructions)
        owner = github_repo_info.get('owner')
        repo = github_repo_info.get('name')
        github_access_token = user.get('github_access_token')
        public_key = instructions['id_rsa_public']

        response = self.push_keys_into_api_and_get_response(
            title,
            owner,
            repo,
            public_key,
            github_access_token,
        )

        if response_did_succeed(response):
            instructions['github_deploy_key'] = response.json()
            build.append_to_stdout(
                "Keys pushed to github successfully!!!!!")
        else:
            self.dump_error_into_build_output(build, response)

        self.produce(instructions)


class LocalRetrieve(CarpentryPipelineStep):
    def ensure_builddir(self, build, instructions):
        slug = instructions['slug']
        workdir = conf.workdir_node.join(slug)
        build_dir = conf.build_node.join(slug)

        instructions['workdir'] = workdir
        instructions['build_dir'] = build_dir

        if not os.path.exists(build_dir):
            os.makedirs(build_dir)

        shutil.rmtree(build_dir)

        os.makedirs(build_dir)
        return build_dir, instructions

    def run_git_clone(self, build, build_dir, instructions):
        git = render_string(conf.git_executable_path + ' clone -b {branch} {git_uri} ' + build_dir, instructions)

        timeout_in_seconds = int(instructions.get('git_clone_timeout_in_seconds') or 0)
        # TODO: sanitize the git url before using it, avoid shell injection :O
        process = run_command(git, chdir=build_dir, environment={
            # http://stackoverflow.com/questions/14220929/git-clone-with-custom-ssh-using-git-ssh-error/27607760#27607760
            'GIT_SSH_COMMAND': render_string(conf.ssh_executable_path + " -o StrictHostKeyChecking=no -i {id_rsa_private_key_path}", instructions),
        })

        stdout, exit_code = stream_output(self, process, build, timeout_in_seconds=timeout_in_seconds)
        exit_code = int(exit_code)
        if exit_code != 0:
            build.set_status('failed')
            build.append_to_stdout("Failed to {0}\n".format(git))
            build.append_to_stdout(force_unicode(stdout))
            build.append_to_stdout("\n")

        return stdout, exit_code, instructions

    def run_git_checkout(self, build, build_dir, instructions):
        checkout = render_string(conf.git_executable_path + ' checkout {commit}', instructions)
        process = run_command(checkout, chdir=build_dir)

        timeout_in_seconds = int(instructions.get('git_clone_timeout_in_seconds') or 0)

        stdout, exit_code = stream_output(self, process, build, timeout_in_seconds=timeout_in_seconds)
        return stdout, exit_code, instructions

    def consume(self, instructions):
        build = set_build_status(instructions, 'retrieving')
        build.append_to_stdout('retrieving repo...\n')
        build_dir, instructions = self.ensure_builddir(build, instructions)

        stdout, exit_code, instructions = self.run_git_clone(build, build_dir, instructions)

        if int(exit_code) != 0:
            build.set_status('failed')
            self.log('Git clone failed {0}'.format(stdout))
            return

        # checking out a specific commit
        if instructions.get('commit', False):
            stdout, exit_code, instructions = self.run_git_checkout(build, build_dir, instructions)
            if exit_code != 0:
                build.set_status('failed')
                self.log('Git checkout failed {0}'.format(stdout))
                return

        git_show = conf.git_executable_path + ' show HEAD'
        try:
            git_show_stdout = check_output(git_show, cwd=build_dir, shell=True)
            build.append_to_stdout(force_unicode(git_show_stdout))

        except CalledProcessError as e:
            build.append_to_stdout(b'Failed to retrieve commit information\n')
            build.append_to_stdout(b'-----------------\n')
            build.append_to_stdout(force_unicode(traceback.format_exc(e)))
            build.set_status('failed')
            self.log('git-show failed {0}'.format(stdout))
            return

        author = AUTHOR_REGEX.search(git_show_stdout)
        commit = COMMIT_REGEX.search(git_show_stdout)
        message = COMMIT_MESSAGE_REGEX.search(git_show_stdout)
        meta = {}

        if commit:
            build.commit = commit.group('commit')
            meta.update(commit.groupdict())

        if author:
            build.author_name = author.group('name')
            build.author_email = author.group('email')
            meta.update(author.groupdict())

        if message:
            build.commit_message = message.group('commit_message')
            meta.update(message.groupdict())

        build.save()
        self.log("meta: %s", meta)
        instructions['git'] = meta
        self.produce(instructions)


class CheckAndLoadBuildFile(CarpentryPipelineStep):
    def consume(self, instructions):
        set_build_status(instructions, 'checking')
        b = Build.objects.get(id=instructions['id'])
        b.stdout += 'checking .carpentry.yml...\n'
        b.save()

        build_dir = instructions['build_dir']
        yml_path = os.path.join(build_dir, '.carpentry.yml')

        if not os.path.exists(yml_path):
            instructions['build'] = {'shell': instructions['shell_script']}
            b.append_to_stdout('.carpentry.yml not found, using provided shell_script\n')

            return self.produce(instructions)

        with codecs.open(yml_path, 'r', 'utf-8') as fd:
            raw_yml = fd.read()

        self.log("Successfully loaded {0}".format(yml_path))
        b.append_to_stdout('.carpentry.yml successfully loaded\n')

        build = yaml.load(raw_yml)
        instructions['build'] = build

        builder = b.builder
        builder.shell_script = instructions['shell_script']
        builder.save()

        self.produce(instructions)


class DockerDependencyRunner(CarpentryPipelineStep):
    def consume(self, instructions):
        build = set_build_status(instructions, 'running', 'looking for dependency docker images')

        build_info = instructions['build']
        if 'dependencies' not in build_info.keys():
            tmpl = 'not running docker dependencies because they were not set in {0}'
            msg = tmpl.format(json.dumps(build_info, indent=2))
            logging.warning(msg, msg)
            build.append_to_stdout(msg)
            return self.produce(instructions)

        dependency_containers = []
        instructions['dependency_containers'] = dependency_containers

        build = Build.objects.get(id=instructions['id'])
        for dependency in build_info['dependencies']:
            build.append_to_stdout("Running dependency:\n")
            build.append_to_stdout(json.dumps(dependency, indent=2))
            build.append_to_stdout("\n\n")
            container = self.run_dependency(build, dependency)
            dependency_containers.append(container)

        instructions['dependency_containers'] = dependency_containers
        self.produce(instructions)

    def run_dependency(self, build, dependency):
        docker = get_docker_client()

        image = dependency['image']

        for line in docker.pull(image, stream=True):
            build.append_to_stdout(line)
            build.append_to_stdout("\n")
            logging.info("docker pull {0}: {1}".format(image, line))

        hostname = dependency['hostname']

        container = docker.create_container(
            image=image,
            name=hostname,
            hostname=hostname,
            environment=dependency.get('environment', {}),
            detach=True,
        )

        docker.start(container['Id'])
        time.sleep(3)

        dependency['container'] = container
        return dependency


class DockerDependencyStopper(CarpentryPipelineStep):
    def consume(self, instructions):
        build = get_build_from_instructions(instructions)
        if 'dependency_containers' not in instructions:
            msg = render_string('skipping docker dependency stop for {name}', instructions)
            logging.info(msg)
            build.append_to_stdout(msg)
            return self.produce(instructions)

        docker = get_docker_client()

        build = Build.objects.get(id=instructions['id'])
        for dependency in instructions['dependency_containers']:
            container = dependency['container']

            build.append_to_stdout("Stopping dependency:\n")
            build.append_to_stdout(json.dumps(dependency, indent=2))
            build.append_to_stdout("\n\n")
            try:
                docker.stop(container['Id'])
                docker.remove_container(container['Id'], force=True)
            except Exception as e:
                build.append_to_stdout(traceback.format_exc(e))
                build.append_to_stdout("\n\n")

        self.produce(instructions)

    def run_dependency(self, dependency):
        docker = get_docker_client()
        container = docker.create_container(
            image=dependency['image'],
            name=dependency['hostname'],
            hostname=dependency['hostname'],
            detach=True
        )
        docker.start(container['Id'])
        return container


class PrepareShellScript(CarpentryPipelineStep):
    def write_script_to_fd(self, fd, template, instructions):
        rendered = render_string(template, instructions)
        self.log(rendered.strip())
        fd.write(rendered)
        fd.write('\n')

    def consume(self, instructions):
        build = set_build_status(instructions, 'preparing')
        build_dir = instructions['build_dir']
        shell_script_path = os.path.join(build_dir, render_string('.carpentry.{slug}.shell.sh', instructions))
        instructions['shell_script_path'] = shell_script_path

        build.append_to_stdout('wrote {0}...\n'.format(shell_script_path))

        self.log(render_string('writing {shell_script_path}', instructions))

        shell_script = instructions['build']['shell']

        with io.open(shell_script_path, 'wb') as fd:
            self.write_script_to_fd(fd, "#!/bin/bash", instructions)
            self.write_script_to_fd(fd, "set -e", instructions)
            self.write_script_to_fd(fd, shell_script, instructions)

        build.append_to_stdout('---------------------------\n')
        build.append_to_stdout('build script:\n')
        build.append_to_stdout('---------------------------\n\n')
        build.append_to_stdout(shell_script)
        build.append_to_stdout('\n\n')
        build.append_to_stdout('---------------------------\n')

        os.chmod(shell_script_path, 0755)

        self.produce(instructions)


class RunBuild(CarpentryPipelineStep):
    def consume(self, instructions):
        set_build_status(instructions, 'running')

        if 'image' not in instructions['build']:
            self.build_native(instructions)
        else:
            self.build_with_docker(instructions)

    def build_with_docker(self, instructions):
        DOCKERFILE_TEMPLATE = '\n'.join([
            'FROM {build[image]}',
            'CMD ["bash", "{shell_script_path}"]'
        ])
        build_dir = instructions['build_dir']
        dockerfile_path = os.path.join(build_dir, 'Dockerfile')

        with io.open(dockerfile_path, 'wb') as fd:
            rendered_dockerfile = render_string(DOCKERFILE_TEMPLATE, instructions)
            fd.write(rendered_dockerfile)

        docker = get_docker_client()
        commit = instructions['commit']
        slug = instructions['slug']
        image_tag = ':'.join([slug, commit[:8]])

        build = Build.get(id=instructions['id'])

        for line in docker.build(path=build_dir,
                                 rm=True,
                                 forcerm=True,
                                 stream=True,
                                 tag=image_tag):
            build.append_to_stdout(line)

        container_links = [(d['image'], d['hostname']) for d in instructions['dependency_containers']]

        container = docker.create_container(
            image=image_tag,
            environment=instructions['build'].get('environment', {}),
            host_config=create_host_config(
                links=container_links
            ),
            name=image_tag,
        )
        docker.start(container['Id'])

        for line in docker.logs(container['Id'], stream=True, stdout=True):
            build.append_to_stdout(line)

        build.code = docker.wait(container)

        if build.code == 0:
            build.set_status('succeeded')
        else:
            build.set_status('failed')

        instructions['container'] = container
        self.produce(instructions)

    def build_native(self, instructions):
        cmd = render_string('bash {shell_script_path}', instructions)

        self.log(render_string("running: bash {shell_script_path}", instructions))
        self.log(render_string("cwd: {build_dir}", instructions))

        process = run_command(cmd, chdir=instructions['build_dir'])

        b = Build.get(id=instructions['id'])
        b.append_to_stdout('running {0}...\n'.format(cmd))
        b.save()

        timeout_in_seconds = instructions.get('build_timeout_in_seconds')
        stdout, exit_code = stream_output(self, process, b, timeout_in_seconds=timeout_in_seconds)
        b.append_to_stdout(force_unicode(stdout))
        b.code = int(exit_code)
        b.date_finished = datetime.utcnow()
        b.save()
        now = datetime.utcnow()

        if b.code == 0:
            status = 'succeeded'
        else:
            status = 'failed'

        instructions['status'] = status
        self.log(render_string("build of {name} {status}", instructions))

        msg = 'carpentry build {0} at {1} UTC'.format(
            status,
            now.strftime('%Y/%m/%d %H:%M:%S')
        )
        set_build_status(instructions, status, msg)
        self.produce(instructions)
