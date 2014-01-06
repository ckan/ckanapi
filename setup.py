#!/usr/bin/env python

from setuptools import setup

setup(name='ckanapi',
      version='3.0-dev',
      description='Thin wrapper around the CKAN Action API',
      author='Ian Ward',
      author_email='ian@excess.org',
      url='https://github.com/open-data/ckanapi',
      packages=['ckanapi', 'ckanapi.tests'],
      test_suite='ckanapi.tests',
      zip_safe=False,
     )
