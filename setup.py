#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

requirements = [
    'tumbler==0.0.19',
    'cqlengine==0.21.0',
    'blist==1.3.6',
    'bcrypt==1.1.1',
    'ansiconv==1.0.0',
    'gunicorn==19.3.0',
    'ansi2html==1.1.0',
    'lineup==0.1.4',
    'python-dateutil==2.4.2',
]

setup(
    name='jaci',
    version='0.0.0',
    description='Jaci',
    entry_points={
        'console_scripts': ['jaci = jaci.cli:main'],
    },
    author='Gabriel Falcao',
    author_email='gabriel@nacaolivre.org',
    url='http://falcao.it/jaci',
    packages=find_packages(exclude=['*tests*']),
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
)
