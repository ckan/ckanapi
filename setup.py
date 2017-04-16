#!/usr/bin/env python

from setuptools import setup
import sys


install_requires=[
    'setuptools',
    'docopt',
    'requests',
    #'-e git://github.com/sigmavirus24/requests.git@537de1c65137c39b15277c6dc11aa932f82ed7c0#egg=requests',
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

