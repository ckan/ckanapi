## ckanapi

A [command line interface](#ckanapi-cli) and
[Python module](#ckanapi-python-module) for accessing the
[CKAN Action API](http://docs.ckan.org/en/latest/api/index.html#action-api-reference)

[![Build Status](https://travis-ci.org/ckan/ckanapi.png?branch=master)](https://travis-ci.org/ckan/ckanapi) tested under Python 2.7, 3.6 and pypy

## Installation

```
pip install ckanapi
```


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

Use -r to specify the remote CKAN instance, and -a to provide an
API KEY. Remote actions connect as an anonymous user by default.

Local CKAN actions may be run by specifying the config file with -c.
If no remote server or config file is specified the CLI will look for
a development.ini file in the current directory, much like paster
commands.

Local CKAN actions are performed by the site user (default system
administrator) when -u is not specified.

To perform local actions with a less privileged user use
the -u option with a user name or a name that doesn't exist. This is
useful if you don't want things like deleted datasets or private
information to be returned.


### Action Arguments

Simple action arguments may be passed in KEY=STRING form for string
values or in KEY:JSON form for JSON values.

E.g. to view a dataset using a KEY=STRING parameter:

```
$ ckanapi action package_show id=my-dataset-name
{
  "name": "my-dataset-name",
  ...
}

```

E.g. to get the number of datasets for each organization
using KEY:JSON parameters:

```
$ ckanapi action package_search 'facet.field:["organization"]' rows:0
{
  "facets": {
    "organization": {
      "org1": 42,
      "org2": 21,
      ...
    }
  },
  ...
}
```

Files may be passed for upload using the KEY@FILE form.

E.g. create a resource with a file attached

```
$ ckanapi resource_create package_id=my-dataset-with-files \
          upload@/path/to/file/to/upload.csv \
          url=dummy-value  # ignored but required by CKAN<2.6
```

### Bulk Dumping and Loading Operations

Datasets, groups, organizations, users and related items may be dumped to
[JSON lines](http://jsonlines.org)
text files and created or updated from JSON lines text files.

E.g. dumping datasets from CKAN into a local file with 4 processes:

```
$ ckanapi dump datasets --all -O datasets.jsonl.gz -z -p 4 -r http://localhost
```

E.g. load datasets from a dataset dump file with 3 processes in parallel:

```
$ ckanapi load datasets -I datasets.jsonl.gz -z -p 3 -c /etc/ckan/production.ini
```

These bulk dumping and loading jobs can be run in parallel with
multiple worker processes. The jobs in progress, the rate of job
completion and any individual errors are shown on STDERR while
the jobs run.

Bulk loading jobs may be resumed from the last completed
record or split across multiple servers by specifying record
start and max values.


### Bulk Delete

Datasets, groups, organizations, users and related items may be deleted in
bulk with the delete command. This command accepts ids or names on the
command line or a number of different formats piped on standard input.

Delete all the datasets (JSON list of "id" or "name" values)
```
$ ckanapi action package_list -j | ckanapi delete datasets
```

Selective delete (JSON object with "results" list containing "id" values)
```
$ ckanapi action package_search q=ponies | ckanapi delete datasets
```

Processed JSON Lines (JSON objects with "id" or "name" value, one per line)
```
$ ckanapi dump groups --all > groups.jsonl
$ grep ponies groups.jsonl | ckanapi delete groups
```

Simple list of "id" or "name" values (one per line)
```
$ cat users_to_remove.txt
fred
bill
larry
$ ckanapi delete users < users_to_remove.txt
```


### Bulk Dataset and Resource Export - datapackage.json format

Datasets may be exported to a simplified
[datapackage.json format](http://dataprotocols.org/data-packages/)
(which includes the actual resources, where available).

If the resource url is not available, the resource will be included
in the datapackage.json file but the actual resource data will not be downloaded.

```
$ ckanapi dump datasets --all --datapackages=./output_directory/ -r http://sourceckan.example.com
```

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
from ckanapi import RemoteCKAN
ua = 'ckanapiexample/1.0 (+http://example.com/my/website)'

demo = RemoteCKAN('http://demo.ckan.org', user_agent=ua)
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

All actions in the [CKAN Action API](http://docs.ckan.org/en/latest/api/index.html#action-api-reference)
and actions added by CKAN plugins are supported by action shortcuts and
`call_action` calls.

Many CKAN API functions can only be used by authenticated users. Use the
`apikey` parameter to supply your CKAN API key to `RemoteCKAN`:

    demo = RemoteCKAN('http://demo.ckan.org', apikey='MY-SECRET-API-KEY')


### Exceptions

* `NotAuthorized` - user unauthorized or accessing a deleted item
* `NotFound` - name/id not found
* `ValidationError` - field errors listed in `.error_dict`
* `SearchQueryError` - error reported from SOLR index
* `SearchError`
* `CKANAPIError` - incorrect use of ckanapi or unable to parse response
* `ServerIncompatibleError` - the remote API is not a CKAN API

When using an action shortcut or the `call_action` method
failures are raised as exceptions just like when calling `get_action` from a
CKAN plugin:

```python
from ckanapi import RemoteCKAN, NotAuthorized
ua = 'ckanapiexample/1.0 (+http://example.com/my/website)'

demo = RemoteCKAN('http://demo.ckan.org', apikey='phony-key', user_agent=ua)
try:
    pkg = demo.action.package_create(name='my-dataset', title='not going to work')
except NotAuthorized:
    print 'denied'
```

When it is possible to `import ckan` all the ckanapi exception classes are
replaced with the CKAN exceptions with the same names.


### File uploads

File uploads for CKAN 2.2+ are supported by passing file-like objects to action
shortcut methods:

```python
from ckanapi import RemoteCKAN
ua = 'ckanapiexample/1.0 (+http://example.com/my/website)'

mysite = RemoteCKAN('http://myckan.example.com', apikey='real-key', user_agent=ua)
mysite.action.resource_create(
    package_id='my-dataset-with-files',
    url='dummy-value',  # ignored but required by CKAN<2.6
    upload=open('/path/to/file/to/upload.csv', 'rb'))
```

When using `call_action` you must pass file objects separately:

```python
mysite.call_action('resource_create',
    {'package_id': 'my-dataset-with-files'},
    files={'upload': open('/path/to/file/to/upload.csv', 'rb')})
```

### Session Control

As of ckanapi 4.0 RemoteCKAN will keep your HTTP connection open using a
[requests session](http://docs.python-requests.org/en/master/user/advanced/).

For long-running scripts make sure to close your connections by using
RemoteCKAN as a context manager:

```python
from ckanapi import RemoteCKAN
ua = 'ckanapiexample/1.0 (+http://example.com/my/website)'

with RemoteCKAN('http://demo.ckan.org', user_agent=ua) as demo:
    groups = demo.action.group_list(id='data-explorer')
print groups
```

Or by explicitly calling `RemoteCKAN.close()`.

### LocalCKAN

A similar class is provided for accessing local CKAN instances from a plugin in
the same way as remote CKAN instances.
Unlike [CKAN's get_action](http://docs.ckan.org/en/latest/extensions/plugins-toolkit.html?highlight=get_action#ckan.plugins.toolkit.get_action)
LocalCKAN prevents data from one action
call leaking into the next which can cause issues that are very hard do debug.

This class defaults to using the site user with full access.

```python
from ckanapi import LocalCKAN, ValidationError

registry = LocalCKAN()
try:
    registry.action.package_create(name='my-dataset', title='this will work fine')
except ValidationError:
    print 'unless my-dataset already exists'
```

For extra caution pass a blank username to LocalCKAN and only actions allowed
by anonymous users will be permitted.

```python
from ckanapi import LocalCKAN

anon = LocalCKAN(username='')
print anon.action.status_show()
```

### TestAppCKAN

A class is provided for making action requests to a
[webtest.TestApp](http://webtest.readthedocs.org/en/latest/testapp.html)
instance for use in CKAN tests:

```python
from ckanapi import TestAppCKAN
from webtest import TestApp

test_app = TestApp(...)
demo = TestAppCKAN(test_app, apikey='my-test-key')
groups = demo.action.group_list(id='data-explorer')
```


## License

🇨🇦 Government of Canada / Gouvernement du Canada

The project files are covered under Crown Copyright, Government of Canada
and is distributed under the MIT license. Please see [COPYING](COPYING) /
[COPYING.fr](COPYING.fr) for full details.
