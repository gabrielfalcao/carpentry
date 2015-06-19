#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import os
import io
import codecs
import yaml
from jaci import conf
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT
from lineup import Step
from jaci.util import calculate_redis_key, render_string
from jaci.models import Build


def run_command(command, chdir):
    return Popen(command, stdout=PIPE, stderr=STDOUT, shell=True, cwd=chdir)


def stream_output(step, process, redis_stdout_key):
    stdout = []
    attemps = 0
    while attemps < 10:
        out = process.stdout.readline() or ''
        # err = process.stderr.readline() or ''

        if not out:  # and not err:
            attemps += 1
            continue

        step.backend.redis.append(redis_stdout_key, out)
        stdout.append(out)
        # self.backend.redis.append(redis_stderr_key, err)

    exit_code = process.returncode or 0
    return '\n'.join(stdout), exit_code


class PrepareSSHKey(Step):
    def after_consume(self, instructions):
        path = render_string('{slug}-id_rsa', instructions)
        msg = "The SSH key is in place: {0}".format(path)
        self.log(msg)

    def before_consume(self):
        self.log("ready to place ssh keys")

    def write_file(self, path, filename, contents):
        if not os.path.exists(path):
            os.makedirs(path)

        destination = os.path.join(path, filename)
        with io.open(destination, 'wb') as fd:
            fd.write(contents)

    def consume(self, instructions):
        private_key = instructions['id_rsa_private']
        public_key = instructions['id_rsa_public']

        id_rsa_private_key_path = render_string('{slug}-id_rsa', instructions)
        id_rsa_public_key_path = render_string('{slug}-id_rsa.pub', instructions)
        instructions['id_rsa_private_key_path'] = id_rsa_private_key_path
        instructions['id_rsa_public_key_path'] = id_rsa_public_key_path

        slug = instructions['slug']
        workdir = conf.build_node.join('builds/{0}'.format(slug))

        ssh_dir = conf.workdir_node.join('ssh-keys/{0}'.format(slug))
        self.write_file(ssh_dir, id_rsa_private_key_path, private_key)
        self.write_file(ssh_dir, id_rsa_public_key_path, public_key)

        redis_stdout_key, redis_stderr_key = calculate_redis_key(instructions)
        instructions['redis_stdout_key'] = redis_stdout_key
        instructions['redis_stderr_key'] = redis_stderr_key

        instructions['ssh_dir'] = ssh_dir
        instructions['workdir'] = workdir

        self.produce(instructions)


class LocalRetrieve(Step):
    def after_consume(self, instructions):
        msg = render_string("Done git cloning {git_uri}", instructions)
        self.log(msg)

    def before_consume(self):
        self.log("ready to git clone")

    def consume(self, instructions):
        slug = instructions['slug']
        workdir = conf.workdir_node.join(slug)
        build_dir = conf.build_node.join(slug)

        redis_stdout_key, redis_stderr_key = calculate_redis_key(instructions)
        instructions['redis_stdout_key'] = redis_stdout_key
        instructions['redis_stderr_key'] = redis_stderr_key
        instructions['workdir'] = workdir
        instructions['build_dir'] = build_dir

        if os.path.exists(build_dir):
            git = '/usr/bin/env git pull'
            chdir = build_dir
        else:
            git = render_string('/usr/bin/env git clone {git_uri} ' + build_dir, instructions)
            chdir = conf.workdir.path

        # TODO: sanitize the git url before using it, avoid shell injection :O
        process = run_command(git, chdir=chdir)

        stdout, exit_code = stream_output(self, process, redis_stdout_key)
        instructions['git'] = {
            'stdout': stdout,
            'exit_code': exit_code,
        }

        b = Build.objects.get(id=instructions['id'])
        if b.stdout is None:
            b.stdout = ''

        b.stdout += stdout
        b.code = int(exit_code)
        b.save()

        self.produce(instructions)


class CheckAndLoadBuildFile(Step):
    def before_consume(self):
        self.log("ready to load .jaci.yml")

    def consume(self, instructions):
        build_dir = instructions['build_dir']
        yml_path = os.path.join(build_dir, '.jaci.yml')

        if not os.path.exists(yml_path):
            instructions['build'] = {'shell': 'ls'}
            return self.produce(instructions)

        with codecs.open(yml_path, 'r', 'utf-8') as fd:
            raw_yml = fd.read()

        build = yaml.load(raw_yml)
        instructions['build'] = build

        self.produce(instructions)


class PrepareShellScript(Step):
    def after_consume(self, instructions):
        msg = "Shell script ready"
        self.log(msg)

    def before_consume(self):
        self.log("ready to write shell scripts")

    def consume(self, instructions):
        build_dir = instructions['build_dir']
        shell_script_path = os.path.join(build_dir, render_string('.{slug}.shell.sh', instructions))
        with io.open(shell_script_path, 'wb') as fd:
            # os.fchmod(fd, 755)
            fd.write("#!/bin/bash\n")
            fd.write(instructions['build']['shell'])

        instructions['shell_script_path'] = shell_script_path
        self.produce(instructions)


class LocalBuild(Step):
    def after_consume(self, instructions):
        msg = render_string("Done testing {name}", instructions)
        self.log(msg)

    def before_consume(self):
        self.log("ready to run builds")

    def consume(self, instructions):
        ls = 'ls'
        process = run_command(ls, chdir=instructions['build_dir'])
        redis_stdout_key, redis_stderr_key = calculate_redis_key(instructions)

        stdout, exit_code = stream_output(self, process, redis_stdout_key)
        instructions['shell'] = {
            'stdout': stdout,
            'exit_code': exit_code,
        }

        b = Build.objects.get(id=instructions['id'])
        if b.stdout is None:
            b.stdout = ''

        b.stdout += stdout
        b.code = int(exit_code)
        b.date_finished = datetime.utcnow()
        b.save()

        self.produce(instructions)
