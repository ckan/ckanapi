## ckanapi

A [command line interface](#ckanapi-cli) and
[Python module](#ckanapi-python-module) for accessing the
[CKAN Action API](http://docs.ckan.org/en/latest/api.html)

[![Build Status](https://travis-ci.org/ckan/ckanapi.png?branch=master)](https://travis-ci.org/ckan/ckanapi) tested under Python 2.6, 2.7, 3.2, 3.3 and pypy

## ckanapi CLI

The ckanapi command line interface lets you access local and
remote CKAN instances for bulk operations and simple API actions.


### Actions

Simple actions with string parameters may be called directly. The
response is pretty-printed to STDOUT. e.g.:

```
$ ckanapi action group_list -r http://demo.ckan.org
[
  "data-expolorer",
  "example-group",
  "geo-examples",
  ...
]
```

Local CKAN actions may be run by specifying the config file with -c.
If no remote server or config file is specified the CLI will look for
a development.ini file in the current directory, much like paster
commands. When connecting to a local CKAN instance the site user
(sysadmin) is used by default.


### Bulk operations

Datasets, groups and organizations may be dumped to
[JSON lines](http://jsonlines.org)
text files and created or updated from JSON lines text files.
These bulk dumping and loading jobs can be run in parallel with
multiple worker processes. The jobs in progress, the rate of job
completion and any individual errors are shown on STDERR while
the jobs run.

e.g. load datasets from a dataset dump file with 3 processes in parallel:

```
$ ckanapi load datasets -I datasets.jsonl.gz -z -p 3 -c /etc/ckan/production.ini
```

Bulk loading jobs may be resumed from the last completed
record or split across multiple servers by specifying record
start and max values.


### Shell pipelines

Simple shell pipelines are possible with the CLI. E.g. update the
title of a dataset with the help of the 'jq' command-line json tool:

```
$ ckanapi action package_show id=my-dataset \
  | jq '.+{"title":"New title"}' \
  | ckanapi action package_update -i
```

E.g. Copy all datasets from one CKAN instance to another:

```
$ ckanapi dump datasets --all -q -r http://sourceckan.example.com \
  | ckanapi load datasets
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

The example above is using an "action shortcut". The `.action` object detects
the method name used ("group_list" above) and converts it to a normal
`call_action` call. This is equivalent code without using an action shortcut:

```python
groups = demo.call_action('group_list', {'id': 'data-explorer'})
```

All actions in the [CKAN Action API](http://docs.ckan.org/en/latest/api.html)
and actions added by CKAN plugins are supported by action shortcuts and
`call_action` calls.


### Exceptions

* `NotAuthorized` - user unauthorized or accessing a deleted item
* `NotFound` - name/id not found
* `ValidationError` - field errors listed in `.error_dict`
* `SearchQueryError` - error reported from SOLR index
* `SearchError`
* `CKANAPIError` - incorrect use of ckanapi or unable to parse response

When using an action shortcut or the `call_action` method
failures are raised as exceptions just like when calling `get_action` from a
CKAN plugin:

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

When it is possible to `import ckan` all the ckanapi exception classes are
replaced with the CKAN exceptions with the same names.


### File uploads

File uploads for CKAN 2.2+ are supported by passing file-like objects to action
shortcut methods:

```python
import ckanapi

mysite = ckanapi.RemoteCKAN('http://myckan.example.com',
    apikey='real-key',
    user_agent='ckanapiexample/1.0 (+http://example.com/my/website)')
mysite.action.resource_create(
    package_id='my-dataset-with-files',
    upload=open('/path/to/file/to/upload.csv'))
```

When using `call_action` you must pass file objects separately:

```python
mysite.call_action('resource_create',
    {'package_id': 'my-dataset-with-files'},
    files={'upload': open('/path/to/file/to/upload.csv')})
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

A class is provided for making action requests to a
[webtest.TestApp](http://webtest.readthedocs.org/en/latest/testapp.html)
instance for use in CKAN tests:

```python
import ckanapi
import webtest

test_app = webtest.TestApp(...)
demo = ckanapi.TestAppCKAN(test_app, apikey='my-test-key')
groups = demo.action.group_list(id='data-explorer')
```
