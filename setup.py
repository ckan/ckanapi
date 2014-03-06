#!/usr/bin/env python

from setuptools import setup

setup(
    name='ckanapi',
    version='3.3-dev',
    description=
        'A command line interface and Python module for '
        'accessing the CKAN Action API',
    license='MIT',
    author='Ian Ward',
    author_email='ian@excess.org',
    url='https://github.com/ckan/ckanapi',
    packages=[
        'ckanapi',
        'ckanapi.tests',
        'ckanapi.tests.mock',
        'ckanapi.cli',
        ],
    test_suite='ckanapi.tests',
    zip_safe=False,
    entry_points = """
        [console_scripts]
        ckanapi=ckanapi.cli.main:main

        [paste.paster_command]
        ckanapi=ckanapi.cli.paster:CKANAPICommand
        """
    )
