#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import io
import os
from plant import Node
from uuid import uuid1
from jaci.models import Builder

ssh_folder = Node(os.path.expanduser('~/.ssh'))


def read_ssh_file(name):
    path = ssh_folder.join(name)
    with io.open(path, 'rb') as fd:
        return fd.read()


def main():
    Builder.create(
        id=uuid1(),
        name=u'Birdseye',
        git_uri='git@github.com:cnry/birdseye.git',
        build_instructions='make test',
        id_rsa_private=read_ssh_file('id_rsa'),
        id_rsa_public=read_ssh_file('id_rsa.pub'),
    )
    Builder.create(
        id=uuid1(),
        name=u'Birdseed',
        git_uri='git@github.com:cnry/birdseed.git',
        build_instructions='make test',
        id_rsa_private=read_ssh_file('id_rsa'),
        id_rsa_public=read_ssh_file('id_rsa.pub'),
    )
    Builder.create(
        id=uuid1(),
        name=u'Ingress',
        git_uri='git@github.com:cnry/ingress.git',
        build_instructions='make test',
        id_rsa_private=read_ssh_file('id_rsa'),
        id_rsa_public=read_ssh_file('id_rsa.pub'),
    )


if __name__ == '__main__':
    main()
