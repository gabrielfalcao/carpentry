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
    finder.visit(ast.parse(local_file('jaci', 'version.py')))
    return finder.version


requirements = [
    'ansi2html==1.1.0',
    'ansiconv==1.0.0',
    'bcrypt==1.1.1',
    'blist==1.3.6',
    'cffi==1.1.2',
    'GitHub-Flask==2.0.1',
    'lineup==0.1.4',
    'milieu==0.1.5',
    'plant==0.1.1',
    'pyOpenSSL==0.15.1',
    'python-dateutil==2.4.2',
    'redis==2.8.0',
    'requests==2.5.1',
    'tumbler==0.0.19',
    'coloredlogs==1.0.1',
    'cqlengine==0.21.0'
]

setup(
    name='jaci',
    version='0.0.14',
    description='continuous integration for the people',
    entry_points={
        'console_scripts': ['jaci = jaci.cli:main'],
    },
    author='Gabriel Falcao',
    author_email='gabriel@nacaolivre.org',
    url='http://falcao.it/jaci',
    packages=find_packages(exclude=['*tests*']),
    # package_data={'jaci': [
    #     'recursive-include jaci/templates *'
    #     'recursive-include jaci/static *'
    # ]},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
)
