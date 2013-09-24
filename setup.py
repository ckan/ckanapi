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
          # See versions here: https://github.com/okfn/ckan/blob/master/requirements.txt
          'ckan',
          'ckanapi',
          'formencode',
          'vdm',
          'sqlalchemy == 0.7.0',
          'PasteDeploy',
          'Pylons==0.9.7',
          'pyutilib.component.core',
          'WebOb==1.0.8',
          'python-dateutil',
          'solrpy',
      ],
      test_suite='tests',
     )
