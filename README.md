## ckanapi

[![Build Status](https://travis-ci.org/open-data/ckanapi.png?branch=master)](https://travis-ci.org/open-data/ckanapi)

A thin wrapper around CKAN's action API

ckanapi may be used from within a plugin or separate from CKAN.

### Making an API Request

```python
import ckanapi
import pprint

demo = ckanapi.RemoteCKAN('http://demo.ckan.org',
    user_agent='foobot/1.0 (+http://example.com/my/website)')
groups = demo.action.group_list(id='data-explorer')
pprint.pprint(groups)
```

result:

```
[u'data-explorer', u'example-group', u'geo-examples', u'skeenawild']
```

Failures are raised as exceptions just like when calling get_action from a plugin:

```python
import ckanapi

demo = ckanapi.RemoteCKAN('http://demo.ckan.org', apikey='phony-key',
    user_agent='foobot/1.0 (+http://example.com/my/website)')
try:
    pkg = demo.action.package_create(name='my-dataset', title='not going to work')
except ckanapi.NotAuthorized:
    print 'denied'
```

result:

```
denied
```

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

### Customizing RemoteCKAN

The RemoteCKAN class may be passed a callable to use for making requests.  This
allows using a different library for the request:

```python
import ckanapi
import requests

def requests_ftw(url, data, headers):
    r = requests.post(url, data, headers=headers)
    return r.status_code, r.text

demo = ckanapi.RemoteCKAN('http://demo.ckan.org', request_fn=requests_ftw,
    user_agent='foobot/1.0 (+http://example.com/my/website)')
groups = demo.action.group_list(id='data-explorer')
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
