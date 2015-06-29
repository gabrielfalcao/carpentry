#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import os
import re
import json
import time
import logging
import tempfile
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
from docker.client import Client
from docker.utils import kwargs_from_env, create_host_config

from carpentry.util import render_string, get_docker_client
from carpentry.models import Build, GITHUB_STATUS_MAP
# import unicodedata


AUTHOR_REGEX = re.compile(
    r'Author: (?P<name>[^<]+\s*)[<](?P<email>[^>]+)[>]')

COMMIT_REGEX = re.compile(
    r'commit\s*(?P<commit>\w+)', re.I)

COMMIT_MESSAGE_REGEX = re.compile(
    r'Date:.*?\n\s*(?P<commit_message>.*?)\s*^diff --git', re.M | re.S)


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
    stdout = []
    build.stdout = build.stdout or ''
    build.stderr = build.stderr or ''

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
        build.stderr += out
        stdout.append(out)
        if current_transfered_bytes >= stdout_chunk_size:
            build.save()
            current_transfered_bytes = 0

    timed_out = difference > timeout_in_seconds
    if timed_out:
        out = "Build timed out by {0} seconds".format(difference)
        build.stdout += out
        build.stderr += out

        process.terminate()
        exit_code = 420
    else:
        exit_code = process.wait()

    try:
        return ''.join(stdout), exit_code
    except UnicodeDecodeError:
        return ''.encode('utf-8').join(stdout), exit_code


def get_build_from_instructions(instructions):
    return Build.objects.get(id=instructions['id'])


def set_build_status(instructions, status, description=None):
    build = get_build_from_instructions(instructions)
    build.status = status
    build.save()

    github_status = GITHUB_STATUS_MAP.get(status, None)
    if not github_status:
        logging.info("Skipping set github build status to %s", status)
        return

    github_access_token = instructions['user']['github_access_token']
    build.set_github_status(github_access_token, github_status, description)


class PrepareSSHKey(Step):
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
        b = Build.objects.get(id=instructions['id'])
        b.stdout = b.stdout or 'preparing ssh key...\n'
        b.save()
        now = datetime.utcnow()
        set_build_status(instructions, 'running', 'carpentry build started at {0} UTC'.format(now.strftime('%Y/%m/%d %H:%M:%S')))
        slug = instructions['slug']
        workdir = conf.build_node.join(slug)

        ssh_dir = conf.ssh_keys_node.join(slug)

        private_key = instructions['id_rsa_private']
        public_key = instructions['id_rsa_public']

        id_rsa_private_key_path = render_string('{slug}-id_rsa', instructions)
        id_rsa_public_key_path = render_string('{slug}-id_rsa.pub', instructions)
        instructions['id_rsa_private_key_path'] = os.path.join(ssh_dir, id_rsa_private_key_path)
        instructions['id_rsa_public_key_path'] = os.path.join(ssh_dir, id_rsa_public_key_path)

        if not private_key:
            raise RuntimeError(render_string('the builder {builder_id} does not have a private_key set', instructions))

        if not public_key:
            raise RuntimeError(render_string('the builder {builder_id} does not have a public_key set', instructions))

        self.write_file(ssh_dir, id_rsa_private_key_path, private_key, mode=0600)
        self.write_file(ssh_dir, id_rsa_public_key_path, public_key, mode=0644)

        instructions['ssh_dir'] = ssh_dir
        instructions['workdir'] = workdir
        try:
            instructions['ssh_add'] = check_output(render_string('ssh-add {id_rsa_private_key_path}', instructions), shell=True)
        except CalledProcessError:
            pass
        self.produce(instructions)


class PushKeyToGithub(Step):
    REGEX = re.compile(r'(?P<owner>[\w_-]+)/(?P<repo>[\w_-]+)([.]git)?$')

    def parse_github_repo(self, instructions):
        git_uri = instructions['git_uri']
        found = self.REGEX.search(git_uri)
        if found:
            data = found.groupdict()
            return data['owner'], data['repo']

    def consume(self, instructions):
        b = Build.objects.get(id=instructions['id'])
        b.stdout += "pushing key to github...\n"
        b.save()

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
            "title": "carpentry {0}".format(instructions['name']),
            "key": instructions['id_rsa_public'],
            "read_only": True
        }, indent=2)

        self.log("Pushing deploy keys to github {0}".format(url))
        self.log("Pushing deploy keys to github {0}".format(payload))

        response = requests.post(url, data=payload, headers=headers)
        if int(response.status_code) > 300:
            logging.error("%s: Failed to push deploy key %s", response.status_code, response.text)
            b = Build.objects.get(id=instructions['id'])
            b.stdout = b.stdout or ''
            b.status = 'failed'

            b.stdout += "\n--------------------\n"
            b.stdout += "Failed to push deploy key\n"
            b.stdout += "POST {0}\n".format(url)
            b.stdout += "RESPONSE:\n\n"
            try:
                b.stdout += json.dumps(response.json(), indent=2)
            except Exception as e:
                b.stdout += str(e)
                b.stdout += response.text

            b.stdout += "\n--------------------\n"
            b.save()
        else:
            instructions['github_deploy_key'] = response.json()
            self.log("Keys pushed to github successfully!!!!!")

        self.produce(instructions)


class LocalRetrieve(Step):
    def consume(self, instructions):
        set_build_status(instructions, 'retrieving')
        b = Build.objects.get(id=instructions['id'])
        b.stdout += 'retrieving repo...\n'
        b.save()

        slug = instructions['slug']
        workdir = conf.workdir_node.join(slug)
        build_dir = conf.build_node.join(slug)
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)

        instructions['workdir'] = workdir
        instructions['build_dir'] = build_dir

        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

        os.makedirs(build_dir)
        chdir = build_dir

        # else:
        git = render_string(conf.git_executable_path + ' clone -b {branch} {git_uri} ' + build_dir, instructions)

        timeout_in_seconds = instructions.get('git_clone_timeout_in_seconds')
        # TODO: sanitize the git url before using it, avoid shell injection :O
        process = run_command(git, chdir=chdir, environment={
            # http://stackoverflow.com/questions/14220929/git-clone-with-custom-ssh-using-git-ssh-error/27607760#27607760
            'GIT_SSH_COMMAND': render_string(conf.ssh_executable_path + " -o StrictHostKeyChecking=no -i {id_rsa_private_key_path}", instructions),
        })

        b = Build.get(id=instructions['id'])
        stdout, exit_code = stream_output(self, process, b, timeout_in_seconds=timeout_in_seconds)
        instructions['git-clone'] = {
            'stdout': stdout,
            'exit_code': exit_code,
        }

        if int(exit_code) != 0:
            self.log('Git clone failed {0}'.format(stdout))
            b.stdout = b.stdout or ''
            b.status = 'failed'

            b.stdout += "Failed to {0}\n".format(git)
            b.stdout += force_unicode(stdout)
            b.stdout += "\n"
            b.save()
            raise RuntimeError('git clone failed:\n{0}'.format(stdout))

        # checking out a specific commit
        if instructions.get('commit', False):
            checkout = render_string(conf.git_executable_path + ' checkout {commit}', instructions)
            process = run_command(checkout, chdir=chdir)

            b = Build.get(id=instructions['id'])
            stdout, exit_code = stream_output(self, process, b, timeout_in_seconds=timeout_in_seconds)
            instructions['git-checkout'] = {
                'stdout': stdout,
                'exit_code': exit_code,
            }

            if int(exit_code) != 0:
                self.log('git checkout failed {0}'.format(stdout))
                b.stdout = b.stdout or ''
                b.status = 'failed'

                b.stdout += "Failed to {0}\n".format(git)
                b.stdout += force_unicode(stdout)
                b.stdout += "\n"
                b.save()
                raise RuntimeError('git clone failed:\n{0}'.format(stdout))

        git_show = conf.git_executable_path + ' show HEAD'
        try:
            git_show_stdout = check_output(git_show, cwd=chdir, shell=True)
            b.stdout += force_unicode(git_show_stdout)

        except CalledProcessError as e:
            b.stdout += b'Failed to retrieve commit information\n'
            b.stdout += b'-----------------\n'
            b.stdout += force_unicode(traceback.format_exc(e))

        b.save()

        author = AUTHOR_REGEX.search(git_show_stdout)
        commit = COMMIT_REGEX.search(git_show_stdout)
        message = COMMIT_MESSAGE_REGEX.search(git_show_stdout)
        meta = {}

        if commit:
            b.commit = commit.group('commit')
            meta.update(commit.groupdict())

        if author:
            b.author_name = author.group('name')
            b.author_email = author.group('email')
            meta.update(author.groupdict())

        if message:
            b.commit_message = message.group('commit_message')
            meta.update(message.groupdict())

        b.save()
        self.log("meta: %s", meta)
        instructions['git'] = meta
        self.produce(instructions)


class CheckAndLoadBuildFile(Step):
    def consume(self, instructions):
        set_build_status(instructions, 'checking')
        b = Build.objects.get(id=instructions['id'])
        b.stdout += 'checking .carpentry.yml...\n'
        b.save()

        build_dir = instructions['build_dir']
        yml_path = os.path.join(build_dir, '.carpentry.yml')

        if not os.path.exists(yml_path):
            instructions['build'] = {'shell': instructions['shell_script']}
            b.stdout += '.carpentry.yml not found, using provided shell_script\n'
            b.save()

            return self.produce(instructions)

        with codecs.open(yml_path, 'r', 'utf-8') as fd:
            raw_yml = fd.read()

        self.log("Successfully loaded {0}".format(yml_path))
        b.stdout += '.carpentry.yml successfully loaded\n'
        b.save()

        build = yaml.load(raw_yml)
        instructions['build'] = build

        builder = b.builder
        builder.shell_script = instructions['shell_script']
        builder.save()

        self.produce(instructions)


class DockerDependencyRunner(Step):
    def consume(self, instructions):
        set_build_status(instructions, 'running', 'looking for dependency docker images')

        build_info = instructions['build']
        if 'dependencies' not in build_info.keys():
            msg = 'not running docker dependencies because they were not set in %s'
            logging.warning(msg, json.dumps(build_info, indent=2))
            return

        dependency_containers = []
        instructions['dependency_containers'] = dependency_containers

        build = Build.objects.get(id=instructions['id'])
        for dependency in build_info['dependencies']:
            build.stdout += "Running dependency:\n"
            build.stdout += json.dumps(dependency, indent=2)
            build.stdout += "\n\n"
            build.save()
            container = self.run_dependency(build, dependency)
            dependency_containers.append(container)

        instructions['dependency_containers'] = dependency_containers
        self.produce(instructions)

    def run_dependency(self, build, dependency):
        docker = get_docker_client()

        image = dependency['image']

        for line in docker.pull(image, stream=True):
            build.stdout += line
            build.stdout += "\n"
            build.save()
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


class DockerDependencyStopper(Step):
    def consume(self, instructions):
        if 'dependency_containers' not in instructions:
            msg = render_string('skipping docker dependency stop for {name}', instructions)
            logging.info(msg)
            return

        docker = get_docker_client()

        build = Build.objects.get(id=instructions['id'])
        for dependency in instructions['dependency_containers']:
            container = dependency['container']

            build.stdout += "Running dependency:\n"
            build.stdout += json.dumps(dependency, indent=2)
            build.stdout += "\n\n"
            build.save()
            try:
                docker.stop(container['Id'])
                docker.remove_container(container['Id'], force=True)
            except Exception as e:
                build.stdout += traceback.format_exc(e)
                build.stdout += "\n\n"
                build.save()

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


class PrepareShellScript(Step):
    def write_script_to_fd(self, fd, template, instructions):
        rendered = render_string(template, instructions)
        self.log(rendered.strip())
        fd.write(rendered)
        fd.write('\n')

    def consume(self, instructions):
        set_build_status(instructions, 'preparing')
        build_dir = instructions['build_dir']
        shell_script_path = os.path.join(build_dir, render_string('.carpentry.{slug}.shell.sh', instructions))
        instructions['shell_script_path'] = shell_script_path

        b = Build.objects.get(id=instructions['id'])
        b.stdout += 'wrote {0}...\n'.format(shell_script_path)
        b.save()

        self.log(render_string('writing {shell_script_path}', instructions))

        with io.open(shell_script_path, 'wb') as fd:
            self.write_script_to_fd(fd, "#!/bin/bash", instructions)
            self.write_script_to_fd(fd, "set -e", instructions)
            self.write_script_to_fd(fd, instructions['build']['shell'], instructions)

        b.stdout += '---------------------------\n'
        b.stdout += 'build script:\n'
        b.stdout += '---------------------------\n\n'
        b.stdout += instructions['build']['shell']
        b.stdout += '\n\n'
        b.stdout += '---------------------------\n'
        b.save()

        os.chmod(shell_script_path, 0755)

        self.produce(instructions)


class RunBuild(Step):
    def consume(self, instructions):
        set_build_status(instructions, 'running')

        if 'image' not in instructions:
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
            build.stdout += line
            build.save()

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
            build.stdout += line
            build.save()

        build.code = docker.wait(container)

        if build.code == 0:
            status = 'succeeded'
        else:
            status = 'failed'

        build.status = status
        build.save()

        instructions['container'] = container
        self.produce(instructions)

    def build_native(self, instructions):
        cmd = render_string('bash {shell_script_path}', instructions)

        self.log(render_string("running: bash {shell_script_path}", instructions))
        self.log(render_string("cwd: {build_dir}", instructions))

        process = run_command(cmd, chdir=instructions['build_dir'])

        b = Build.get(id=instructions['id'])
        b.stdout += 'running {0}...\n'.format(cmd)
        b.save()

        timeout_in_seconds = instructions.get('build_timeout_in_seconds')
        stdout, exit_code = stream_output(self, process, b, timeout_in_seconds=timeout_in_seconds)
        instructions['shell'] = {
            'stdout': stdout,
            'exit_code': exit_code,
        }

        b.stdout += force_unicode(stdout)
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


class CreateDockerImage(Step):
    def consume(self, instructions):
        kwargs = kwargs_from_env()
        kwargs['tls'].assert_hostname = False
        docker = Client(**kwargs)
        self.produce(instructions)
