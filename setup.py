#!/usr/bin/env python

from setuptools import setup

setup(name='ckanapi',
      version='2.1',
      description='Thin wrapper around the CKAN Action API',
      author='Ian Ward',
      author_email='ian@excess.org',
      url='https://github.com/open-data/ckanapi',
      py_modules=['ckanapi',],
      install_requires = [
          'ckan',
          'ckanapi',
          'formencode',
          'vdm',
          'sqlalchemy == 0.7.0',
          'paste',
      ],
      test_suite='tests',
     )
