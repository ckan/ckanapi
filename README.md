## ckanapi

A [command line interface](#ckanapi-cli) and
[Python module](#ckanapi-python-module) for accessing the
[CKAN Action API](http://docs.ckan.org/en/latest/api.html)

[![Build Status](https://travis-ci.org/ckan/ckanapi.png?branch=master)](https://travis-ci.org/ckan/ckanapi) tested under Python 2.6, 2.7, 3.2, 3.3 and pypy

## ckanapi CLI

The ckanapi command line interface lets you access local and
remote CKAN instances for bulk operations and simple API actions.

Simple actions with string parameters may be called and the response
is pretty-printed by default.

Datasets, groups and organizations may be dumped to
[JSON lines](http://jsonlines.org)
text files and created or updated from JSON lines text files.
Dumping and loading jobs can be run in parallel with
multiple worker processes. Jobs in progress, the rate of job
completion and errors are shown on stderr and may also be logged.

Loading jobs may be resumed from the last completed
record, or split across multiple servers by specifying record
start and max values.

```
Usage:
  ckanapi action ACTION_NAME
          [KEY=VALUE ... | -i] [-j | -J]
          [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
  ckanapi load (datasets | groups | organizations)
          [-I JSONL_INPUT] [-s START] [-m MAX] [-p PROCESSES] [-l LOG_FILE]
          [-n | -o] [-qwz] [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
  ckanapi dump (datasets | groups | organizations)
          (ID_OR_NAME ... | --all) [-O JSONL_OUTPUT] [-p PROCESSES] [-qwz]
          [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
  ckanapi (-h | --help)
  ckanapi --version

Options:
  -h --help                 show this screen
  --version                 show version
  -a --apikey=APIKEY        API key to use for remote actions
  --all                     all the things
  -c --config=CONFIG        CKAN configuration file for local actions,
                            defaults to ./development.ini if that file exists
  -i --stdin-json           pass json from stdin to action
  -I --input=JSONL_INPUT    input json lines from file instead of stdin
  -j --plain-json           plain json instead of pretty-printed json
  -J --jsonl                format list response as json lines instead of
                            default pretty-printed json format
  -l --log=LOG_FILE         append messages generated to LOG_FILE
  -m --max-records=MAX      exit after processing MAX records
  -n --create-only          create new records, don't update existing records
  -o --update-only          update existing records, don't create new records
  -O --output=JSONL_OUTPUT  output to json lines file instead of stdout
  -p --processes=PROCESSES  set the number of worker processes [default: 1]
  -q --quiet                don't display progress messages
  -r --remote=URL           URL of CKAN server for remote actions
  -s --start-record=START   start from record number START, where the first
                            record is number 1 [default: 1]
  -u --ckan-user=USER       perform actions as user with this name, uses the
                            site sysadmin user when not specified
  -w --worker               launch worker process, used internally by load
                            and dump commands
  -z --gzip                 read/write gzipped data
```

## ckanapi Python Module

The ckanapi Python module may be used from within a
[CKAN extension](http://docs.ckan.org/en/latest/extensions/index.html)
or in a Python 2 or Python 3 application separate from CKAN.

### RemoteCKAN

Making a request:

```python
import ckanapi

demo = ckanapi.RemoteCKAN('http://demo.ckan.org',
    user_agent='ckanapiexample/1.0 (+http://example.com/my/website)')
groups = demo.action.group_list(id='data-explorer')
print groups
```

result:

```
[u'data-explorer', u'example-group', u'geo-examples', u'skeenawild']
```

All actions in the [CKAN Action API](http://docs.ckan.org/en/latest/api.html)
and actions added by CKAN plugins are supported.


### Exceptions

Failures are raised as exceptions just like when calling get_action from a plugin:

* `NotAuthorized` - user unauthorized or accessing a deleted item
* `NotFound` - name/id not found
* `ValidationError` - field errors listed in `.error_dict`
* `SearchQueryError` - error reported from SOLR index
* `SearchError`
* `CKANAPIError` - incorrect use of ckanapi or unable to parse response

```python
import ckanapi

demo = ckanapi.RemoteCKAN('http://demo.ckan.org',
    apikey='phony-key',
    user_agent='ckanapiexample/1.0 (+http://example.com/my/website)')
try:
    pkg = demo.action.package_create(name='my-dataset', title='not going to work')
except ckanapi.NotAuthorized:
    print 'denied'
```


### File uploads

File uploads for CKAN 2.2+ are supported by passing file-like objects:

```python
import ckanapi

mysite = ckanapi.RemoteCKAN('http://myckan.example.com',
    apikey='real-key',
    user_agent='ckanapiexample/1.0 (+http://example.com/my/website)')
mysite.action.resource_create(
    package_id='my-dataset-with-files',
    upload=open('/path/to/file/to/upload.csv'))
```

### LocalCKAN

A similar class is provided for accessing local CKAN instances from a plugin in
the same way as remote CKAN instances.  This class defaults to using the site
user with full access.

```python
import ckanapi

registry = ckanapi.LocalCKAN()
try:
    registry.action.package_create(name='my-dataset', title='this will work fine')
except ckanapi.ValidationError:
    print 'unless my-dataset already exists'
```

### TestAppCKAN

A class is provided for making action requests to a paste.fixture.TestApp
instance for use in CKAN tests:

```python
import ckanapi
import paste.fixture

test_app = paste.fixture.TestApp(...)
demo = ckanapi.TestAppCKAN(test_app, apikey='my-test-key')
groups = demo.action.group_list(id='data-explorer')
```
