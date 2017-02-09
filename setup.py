#!/usr/bin/env python

from setuptools import setup
import sys


install_requires=[
    'setuptools',
    'docopt',
    'requests',
    'requests-toolbelt',
    'clint',
]

if sys.version_info <= (3,):
    install_requires.append('simplejson')


setup(
    name='ckanapi',
    version='4.0',
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
    # A workaround for a bug in setuptools that prevents correct installation
    # of "requests". See http://stackoverflow.com/questions/27497470.
    setup_requires='requests',
    install_requires=install_requires,
    test_suite='ckanapi.tests',
    zip_safe=False,
    entry_points = """
        [console_scripts]
        ckanapi=ckanapi.cli.main:main

        [paste.paster_command]
        ckanapi=ckanapi.cli.paster:CKANAPICommand
        """
    )

