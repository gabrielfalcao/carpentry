#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast
import os
from setuptools import setup, find_packages


local_file = lambda *f: \
    open(os.path.join(os.path.dirname(__file__), *f)).read()


class VersionFinder(ast.NodeVisitor):
    VARIABLE_NAME = 'version'

    def __init__(self):
        self.version = None

    def visit_Assign(self, node):
        try:
            if node.targets[0].id == self.VARIABLE_NAME:
                self.version = node.value.s
        except:
            pass


def read_version():
    finder = VersionFinder()
    finder.visit(ast.parse(local_file('carpentry', 'version.py')))
    return finder.version


requirements = [
    'ansi2html>=1.1.0',
    'ansiconv>=1.0.0',
    'bcrypt>=1.1.1',
    'blist>=1.3.6',
    'cffi>=1.1.2',
    'coloredlogs>=1.0.1',
    'cqlengine>=0.21.0',
    'GitHub-Flask>=2.0.1',
    'jsmin>=2.1.1',
    'lineup>=0.1.7',
    'docker-py>=1.2.3',
    'milieu>=0.1.7',
    'plant>=0.1.2',
    'pycrypto>=2.6',
    'pyOpenSSL>=0.15.1',
    'python-dateutil>=2.4.2',
    'redis>=2.10.3',
    'requests>=2.7.0',
    'tumbler>=0.0.20',
    'Flask-SocketIO>=0.6.0',
]


setup(
    name='carpentry-ci',
    version='0.2.39',
    description='continuous integration for the people',
    entry_points={
        'console_scripts': ['carpentry = carpentry.cli:main'],
    },
    author='Gabriel Falcao',
    author_email='gabriel@nacaolivre.org',
    url='http://falcao.it/carpentry',
    packages=find_packages(exclude=['*tests*']),
    # package_data={'carpentry': [
    #     'recursive-include carpentry/templates *'
    #     'recursive-include carpentry/static *'
    # ]},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
)
