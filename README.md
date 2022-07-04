## ckanapi

A command line interface and Python module for accessing the
[CKAN Action API](http://docs.ckan.org/en/latest/api/index.html#action-api-reference)

- [Installation](https://github.com/ckan/ckanapi/blob/master/README.md#installation)
- [ckanapi CLI](https://github.com/ckan/ckanapi/blob/master/README.md#ckanapi-cli)
  - [Actions](https://github.com/ckan/ckanapi/blob/master/README.md#actions)
  - [Action Arguments](https://github.com/ckan/ckanapi/blob/master/README.md#action-arguments)
  - [Bulk Dumping and Loading](https://github.com/ckan/ckanapi/blob/master/README.md#bulk-dumping-and-loading)
  - [Bulk Delete](https://github.com/ckan/ckanapi/blob/master/README.md#bulk-delete)
  - [Bulk Dataset and Resource Export](https://github.com/ckan/ckanapi/edit/master/README.md#bulk-dataset-and-resource-export---datapackagejson-format)
  - [Batch Actions](https://github.com/ckan/ckanapi/blob/master/README.md#batch-actions)
  - [Shell Pipelines](https://github.com/ckan/ckanapi/blob/master/README.md#shell-pipelines)
- [ckanapi Python Module](https://github.com/ckan/ckanapi/blob/master/README.md#ckanapi-python-module)
  - [RemoteCKAN](https://github.com/ckan/ckanapi/blob/master/README.md#remoteckan)
  - [Exceptions](https://github.com/ckan/ckanapi/blob/master/README.md#exceptions)
  - [File Uploads](https://github.com/ckan/ckanapi/blob/master/README.md#file-uploads)
  - [Session Control](https://github.com/ckan/ckanapi/blob/master/README.md#session-control)
  - [LocalCKAN](https://github.com/ckan/ckanapi/blob/master/README.md#localckan)
  - [TestAppCKAN](https://github.com/ckan/ckanapi/blob/master/README.md#testappckan)
- [Tests](https://github.com/ckan/ckanapi/blob/master/README.md#tests)
- [License](https://github.com/ckan/ckanapi/blob/master/README.md#license)


## Installation

Installation with pip:
```
pip install ckanapi
```

Installation with conda:
```
conda install -c conda-forge ckanapi
```


## ckanapi CLI

The ckanapi command line interface lets you access local and
remote CKAN instances for bulk operations and simple API actions.


### Actions

Simple actions with string parameters may be called directly. The
response is pretty-printed to STDOUT.

#### 🔧 List names of groups on a remote CKAN site

```
$ ckanapi action group_list -r https://demo.ckan.org --insecure
[
  "data-explorer",
  "example-group",
  "geo-examples",
  ...
]
```

Use -r to specify the remote CKAN instance, and -a to provide an
API KEY. Remote actions connect as an anonymous user by default.
For this example, we use --insecure as the CKAN demo uses a
self-signed certificate.

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

Note that all actions in the [CKAN Action API](http://docs.ckan.org/en/latest/api/index.html#action-api-reference)
and actions added by CKAN plugins are supported.


### Action Arguments

Simple action arguments may be passed in KEY=STRING form for string
values or in KEY:JSON form for JSON values.

#### 🔧 View a dataset using a KEY=STRING parameter

```
$ ckanapi action package_show id=my-dataset-name
{
  "name": "my-dataset-name",
  ...
}

```

#### 🔧 Get detailed info about a resource in the datastore

```
$ ckanapi action datastore_info id=my-resource-id-or-alias
{
  "meta": {
    "aliases": [
      "test_alias"
    ],
    "count": 1000,
  ...
}
```

#### 🔧 Get the number of datasets for each organization using KEY:JSON parameters

```
$ ckanapi action package_search facet.field:'["organization"]' rows:0
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

#### 🔧 Create a resource with a file attached

Files may be passed for upload using the KEY@FILE form.

```
$ ckanapi action resource_create package_id=my-dataset-with-files \
          upload@/path/to/file/to/upload.csv
```

#### 🔧 Edit a dataset with a text editor

```
$ ckanapi action package_show id=my-dataset-id > my-dataset.json
$ nano my-dataset.json
$ ckanapi action package_update -I my-dataset.json
$ rm my-dataset.json
```

#### 🔧 Update a single resource field

```
$ ckanapi action resource_patch id=my-resource-id size:42000000
```

### Bulk Dumping and Loading

Datasets, groups, organizations, users and related items may be dumped to
[JSON lines](http://jsonlines.org)
text files and created or updated from JSON lines text files.

`dump` and `load` jobs can be run in parallel with
multiple worker processes using the `-p` parameter. The jobs in progress,
the rate of job completion and any individual errors are shown on STDERR
while the jobs run.

There are no parallel limits when running against a CKAN on localhost.  
When running against a remote site, there's a default limit of 3 worker processes.

The environment variables `CKANAPI_MY_SITES` and`CKANAPI_PARALLEL_LIMIT` can be
used to adjust these limits.  `CKANAPI_MY_SITES` (comma-delimited list of CKAN urls)
will not have the `PARALLEL_LIMIT` applied.

`dump` and `load` jobs may be resumed from the last completed
record or split across multiple servers by specifying record
start and max values.

#### 🔧 Dump datasets from CKAN into a local file with 4 processes

```
$ ckanapi dump datasets --all -O datasets.jsonl.gz -z -p 4 -r http://localhost
```

#### 🔧 Export datasets including private ones using search

```
$ ckanapi search datasets include_private=true -O datasets.jsonl.gz -z \
          -c /etc/ckan/production.ini
```

`search` is faster than `dump` because it calls `package_search` to retrieve
many records per call, paginating automatically.

You may add parameters supported by `package_search` to filter the
records returned.


#### 🔧 Load/update datasets from a dataset JSON lines file with 3 processes

```
$ ckanapi load datasets -I datasets.jsonl.gz -z -p 3 -c /etc/ckan/production.ini
```


### Bulk Delete

Datasets, groups, organizations, users and related items may be deleted in
bulk with the delete command. This command accepts ids or names on the
command line or a number of different formats piped on standard input.

#### 🔧 All datasets (JSON list of "id" or "name" values)
```
$ ckanapi action package_list -j | ckanapi delete datasets
```

#### 🔧 Selective delete (JSON object with "results" list containing "id" values)
```
$ ckanapi action package_search q=ponies | ckanapi delete datasets
```

#### 🔧 Processed JSON Lines (JSON objects with "id" or "name" value, one per line)
```
$ ckanapi dump groups --all > groups.jsonl
$ grep ponies groups.jsonl | ckanapi delete groups
```

#### 🔧 Text list of "id" or "name" values (one per line)
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

### Batch Actions

Run a set of actions from a JSON lines file. For local actions this is much faster than running
`ckanapi action ...` in a shell loop because the local start-up time only happens once.

Batch actions can also be run in parallel with multiple processes and errors logged, just like the
dump and load commands.

#### 🔧 Update a dataset field across a number of datasets
```
$ cat update-emails.jsonl
{"action":"package_patch","data":{"id":"dataset-1","maintainer_email":"new@example.com"}}
{"action":"package_patch","data":{"id":"dataset-2","maintainer_email":"new@example.com"}}
{"action":"package_patch","data":{"id":"dataset-3","maintainer_email":"new@example.com"}}
$ ckanapi batch -I update-emails.jsonl
```

#### 🔧 Replace a set of uploaded files
```
$ cat upload-files.jsonl
{"action":"resource_patch","data":{"id":"408e1b1d-d0ca-50ca-9ae6-aedcee37aaa9"},"files":{"upload":"data1.csv"}}
{"action":"resource_patch","data":{"id":"c1eab17f-c2d0-536d-a3f6-41a3dfe6a2c3"},"files":{"upload":"data2.csv"}}
{"action":"resource_patch","data":{"id":"8ed068c2-4d4c-5f20-90db-39d2d596ce1a"},"files":{"upload":"data3.csv"}}
$ ckanapi batch -I upload-files.jsonl --local-files
```

The `"files"` values in the JSON lines file is ignored unless the `--local-files` parameter is passed.
Paths in the JSON lines file reference files on the local filesystems relative to the current working
directory.

### Shell pipelines

Simple shell pipelines are possible with the CLI.

#### 🔧 Copy the name of a dataset to its title with 'jq'
```
$ ckanapi action package_show id=my-dataset \
  | jq '.+{"title":.name}' \
  | ckanapi action package_update -i
```

#### 🔧 Mirror all datasets from one CKAN instance to another
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

demo = RemoteCKAN('https://demo.ckan.org', user_agent=ua)
groups = demo.action.group_list(id='data-explorer')
print(groups)
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

Once again, all actions in the [CKAN Action API](http://docs.ckan.org/en/latest/api/index.html#action-api-reference)
and actions added by CKAN plugins are supported by action shortcuts and
`call_action` calls.

For example, if the [Showcase](https://github.com/ckan/ckanext-showcase#api) extension is installed:

```python
from ckanapi import RemoteCKAN
ua = 'ckanapiexample/1.0 (+http://example.com/my/website)'

demo = RemoteCKAN('https://demo.ckan.org', user_agent=ua)
showcases= demo.action.ckanext_showcase_list()
print(showcases)
```

Combining query parameters clauses is possible as in the following `package_search` action.  This query combines three clauses that are all satisfied by the single [example dataset](https://demo.ckan.org/dataset/sample-dataset-1) in the Demo CKAN site.

More detailed complex query syntax examples can be found in the [SOLR documentation](https://solr.apache.org/guide/6_6/common-query-parameters.html).

```python
from ckanapi import RemoteCKAN
ua = 'ckanapiexample/1.0 (+http://example.com/my/website)'

demo = RemoteCKAN('https://demo.ckan.org', user_agent=ua)
packages = demo.action.package_search(q='+organization:sample-organization +res_format:GeoJSON +tags:geojson')
print(packages)
```  

Many CKAN API functions can only be used by authenticated users. Use the
`apikey` parameter to supply your CKAN API key to `RemoteCKAN`:

    demo = RemoteCKAN('https://demo.ckan.org', apikey='MY-SECRET-API-KEY')

An example of updating a single field in an existing dataset can be seen in the [Examples directory](examples/update_single_field.py)

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

demo = RemoteCKAN('https://demo.ckan.org', apikey='phony-key', user_agent=ua)
try:
    pkg = demo.action.package_create(name='my-dataset', title='not going to work')
except NotAuthorized:
    print('denied')
```

When it is possible to `import ckan` all the ckanapi exception classes are
replaced with the CKAN exceptions with the same names.


### File Uploads

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

with RemoteCKAN('https://demo.ckan.org', user_agent=ua) as demo:
    groups = demo.action.group_list(id='data-explorer')
print(groups)
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
    print('unless my-dataset already exists')
```

For extra caution pass a blank username to LocalCKAN and only actions allowed
by anonymous users will be permitted.

```python
from ckanapi import LocalCKAN

anon = LocalCKAN(username='')
print(anon.action.status_show())
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


## Tests

To run the tests:

  python setup.py test


## License

🇨🇦 Government of Canada / Gouvernement du Canada

The project files are covered under Crown Copyright, Government of Canada
and is distributed under the MIT license. Please see [COPYING](COPYING) /
[COPYING.fr](COPYING.fr) for full details.
