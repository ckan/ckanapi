"""
Code shared by LocalCKAN, RemoteCKAN and TestCKAN
"""

import json

from ckanapi.errors import (CKANAPIError, NotAuthorized, NotFound,
    ValidationError, SearchQueryError, SearchError, SearchIndexError)

class ActionShortcut(object):
    """
    ActionShortcut(foo).bar(baz=2) <=> foo.call_action('bar', {'baz':2})

    An instance of this class is used as the .action attribute of
    LocalCKAN and RemoteCKAN instances to provide a short way to call
    actions, e.g::

        pkg = demo.action.package_show(id='adur_district_spending')

    instead of::

        pkg = demo.call_action('package_show', {'id':'adur_district_spending'})

    File-like values (objects with a 'read' attribute) are
    sent as file-uploads::

        pkg = demo.action.resource_update(package_id='foo', upload=open(..))

    becomes::

        pkg = demo.call_action('resource_update',
            {'package_id': 'foo'}, files={'upload': open(..)})

    """
    def __init__(self, ckan):
        self._ckan = ckan

    def __getattr__(self, name):
        def action(**kwargs):
            files = {}
            for k, v in kwargs.items():
                if hasattr(v, 'read'):
                    files[k] = v
            if files:
                nonfiles = dict((k, v) for k, v in kwargs.items()
                    if k not in files)
                return self._ckan.call_action(name,
                    data_dict=nonfiles,
                    files=files)
            return self._ckan.call_action(name, data_dict=kwargs)
        return action


def prepare_action(action, data_dict=None, apikey=None, files=None):
    """
    Return action_url, data_json, http_headers
    """
    if not data_dict:
        data_dict = {}
    headers = {}
    if not files:
        data_dict = json.dumps(data_dict).encode('ascii')
        headers['Content-Type'] = 'application/json'
    if apikey:
        apikey = str(apikey)
        headers['X-CKAN-API-Key'] = apikey
        headers['Authorization'] = apikey
    url = 'api/action/' + action
    return url, data_dict, headers


def reverse_apicontroller_action(url, status, response):
    """
    Make an API call look like a direct action call by reversing the
    exception -> HTTP response translation that ApiController.action does
    """
    try:
        parsed = json.loads(response)
        if parsed.get('success'):
            return parsed['result']
        if hasattr(parsed, 'get'):
            err = parsed.get('error', {})
        else:
            err = {}
    except (AttributeError, ValueError):
        err = {}

    etype = err.get('__type')
    emessage = err.get('message', '').split(': ', 1)[-1]
    if etype == 'Search Query Error':
        # I refuse to eval(emessage), even if it would be more correct
        raise SearchQueryError(emessage)
    elif etype == 'Search Error':
        # I refuse to eval(emessage), even if it would be more correct
        raise SearchError(emessage)
    elif etype == 'Search Index Error':
        raise SearchIndexError(emessage)
    elif etype == 'Validation Error':
        raise ValidationError(err)
    elif etype == 'Not Found Error':
        raise NotFound(emessage)
    elif etype == 'Authorization Error':
        raise NotAuthorized(err)

    # don't recognize the error
    raise CKANAPIError(repr([url, status, response]))
