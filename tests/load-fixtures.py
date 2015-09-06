#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import io
import os
from plant import Node
from uuid import uuid1
from carpentry.models import Builder


ssh_folder = Node(os.path.expanduser('~/.ssh'))


def read_ssh_file(name):
    path = ssh_folder.join(name)
    with io.open(path, 'rb') as fd:
        return fd.read()


PYTHON = """
pip install -U pip
pip install virtualenv
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r development.txt || echo OK
make
""".strip()


def main():
    for name in ['client-api', 'viks', 'cauldron', 'moorhen']:
        Builder.create(
            id=uuid1(),
            name=name,
            git_uri='git@github.com:cnry/{0}.git'.format(name),
            shell_script=PYTHON,
            status='ready',
            id_rsa_private=read_ssh_file('id_rsa'),
            id_rsa_public=read_ssh_file('id_rsa.pub'),
        )


if __name__ == '__main__':
    main()
