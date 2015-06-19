#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import os
import io
from jaci import conf
from subprocess import Popen, PIPE, STDOUT
from lineup import Step
from jaci.util import calculate_redis_key, render_string


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
        workdir = conf.node.join('builds/{0}'.format(slug))

        ssh_dir = conf.node.join('ssh-keys/{0}'.format(slug))
        self.write_file(ssh_dir, id_rsa_private_key_path, private_key)
        self.write_file(ssh_dir, id_rsa_public_key_path, public_key)

        redis_stdout_key, redis_stderr_key = calculate_redis_key(instructions)
        instructions['redis_stdout_key'] = redis_stdout_key
        instructions['redis_stderr_key'] = redis_stderr_key

        instructions['ssh_dir'] = ssh_dir
        instructions['workdir'] = workdir

        command = render_string('/usr/bin/env git clone {git_uri} ' + workdir, instructions)
        # TODO: sanitize the git url before using it, avoid shell injection :O
        process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)

        stdout, exit_code = self.stream_output(process, redis_stdout_key)
        instructions['git'] = {
            'stdout': stdout,
            'exit_code': exit_code,
        }
        self.produce(instructions)

    def stream_output(self, process, redis_stdout_key):
        stdout = []
        while True:
            out = process.stdout.readline() or ''
            # err = process.stderr.readline() or ''

            if not out:  # and not err:
                break

            self.backend.redis.append(redis_stdout_key, out)
            stdout.append(out)
            # self.backend.redis.append(redis_stderr_key, err)

        return stdout, process.returncode


class LocalRetrieve(Step):
    def after_consume(self, instructions):
        msg = render_string("Done git cloning {git_uri}", instructions)
        self.log(msg)

    def before_consume(self):
        self.log("ready to git clone")

    def consume(self, instructions):
        slug = instructions['slug']
        workdir = conf.node.join(slug)

        redis_stdout_key, redis_stderr_key = calculate_redis_key(instructions)
        instructions['redis_stdout_key'] = redis_stdout_key
        instructions['redis_stderr_key'] = redis_stderr_key
        instructions['workdir'] = workdir

        command = render_string('/usr/bin/env git clone {git_uri}', instructions)
        # TODO: sanitize the git url before using it, avoid shell injection :O
        process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)

        self.stream_output(process, redis_stdout_key)

    def stream_output(self, process, redis_stdout_key):
        while True:
            out = process.stdout.readline() or ''
            # err = process.stderr.readline() or ''

            if not out:  # and not err:
                break

            self.backend.redis.append(redis_stdout_key, out)
            # self.backend.redis.append(redis_stderr_key, err)


class LocalBuild(Step):
    def after_consume(self, instructions):
        msg = render_string("Done building {git_uri}", instructions)
        self.log(msg)

    def before_consume(self):
        self.log("ready to run builds")

    def consume(self, instructions):
        self.produce(instructions)
