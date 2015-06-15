#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

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
    zip_safe=False,
)
