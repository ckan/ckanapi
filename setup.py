#!/usr/bin/env python

from setuptools import setup

setup(name='ckanapi',
      version='2.4-dev',
      description='Thin wrapper around the CKAN Action API',
      license='BSD',
      author='Ian Ward',
      author_email='ian@excess.org',
      url='https://github.com/open-data/ckanapi',
      packages=['ckanapi', 'ckanapi.tests'],
      test_suite='ckanapi.tests',
      zip_safe=False,
     )
