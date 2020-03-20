#!/usr/bin/env python

from setuptools import setup
import sys


install_requires=[
    'setuptools',
    'docopt',
    'requests',
    'python-slugify>=1.0',
    'six>=1.9,<2.0',
]
tests_require=[
    'pyfakefs==3.6.1',
]

if sys.version_info <= (3,):
    install_requires.append('simplejson')


setup(
    name='ckanapi',
    version='4.3',
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
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite='ckanapi.tests',
    zip_safe=False,
    entry_points = """
        [console_scripts]
        ckanapi=ckanapi.cli.main:main

        [paste.paster_command]
        ckanapi=ckanapi.cli.paster:CKANAPICommand
        """
    )

