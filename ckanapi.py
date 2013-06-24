"""
ckanapi
-------

This module a thin wrapper around the CKAN's action API.
"""

import urllib2
import json

class CKANAPIError(Exception):
    """
    The error raised from RemoteCKAN.call_action when no other error
    is recognized.

    If importing CKAN source fails then new versions of NotAuthorized,
    ValidationError, NotFound, SearchQueryError, SearchError and
    SearchIndexError are created as subclasses of this class so that they
    provide a helpful str() for tracebacks.
    """
    def __str__(self):
        return repr(self.args)

try:
    import ckan

except ImportError:
    # Implement the minimum to be compatible with existing errors
    # without requiring CKAN

    class NotAuthorized(CKANAPIError):
        pass

    class ValidationError(CKANAPIError):
        def __init__(self, error_dict):
            self.error_dict = error_dict
        def __str__(self):
            return repr(self.error_dict)

    class NotFound(CKANAPIError):
        def __init__(self, extra_msg):
            self.extra_msg = extra_msg
        def __str__(self):
            return self.extra_msg

    class SearchQueryError(CKANAPIError):
        pass

    class SearchError(CKANAPIError):
        pass

    class SearchIndexError(CKANAPIError):
        pass

else:
    # import ckan worked, so these must not fail
    from ckan.logic import (NotAuthorized, NotFound, ValidationError)
    from ckan.lib.search import (SearchQueryError, SearchError,
                                 SearchIndexError)


class ActionShortcut(object):
    """
    ActionShortcut(foo).bar(baz=2) <=> foo.call_action('bar', {'baz':2})

    An instance of this class is used as the .action attribute of
    LocalCKAN and RemoteCKAN instances to provide a short way to call
    actions, e.g::

        demo = RemoteCKAN('http://demo.ckan.org')
        pkg = demo.action.package_show(id='adur_district_spending')

    instead of::

        demo = RemoteCKAN('http://demo.ckan.org')
        pkg = demo.call_action('package_show', {'id':'adur_district_spending'})

    """
    def __init__(self, ckan):
        self._ckan = ckan

    def __getattr__(self, name):
        def action(apikey=None, **kwargs):
            return self._ckan.call_action(name, data_dict=kwargs,
                                          apikey=apikey)
        return action


class LocalCKAN(object):
    """
    An interface to calling actions with get_action() for CKAN plugins.

    :param username: perform action as this user, defaults to the site user
                     and stored as self.username
    :param context: a default context dict to use when calling actions,
                    stored as self.context with username added as its 'user'
                    value
    """
    def __init__(self, username=None, context=None):
        from ckan.logic import get_action
        self._get_action = get_action

        if not username:
            username = self.get_site_username()
        self.username = username
        self.context = dict(context or [], user=self.username)
        self.action = ActionShortcut(self)

    def get_site_username(self):
        user = self._get_action('get_site_user')({'ignore_auth': True}, ())
        return user['name']

    def call_action(self, action, data_dict=None, context=None, apikey=None):
        """
        :param action: the action name, e.g. 'package_create'
        :param data_dict: the dict to pass to the action, defaults to {}
        :param context: an override for the context to use for this action,
                        remember to include a 'user' when necessary
        """
        if not data_dict:
            data_dict = []
        if context is None:
            context = self.context
        # copy dicts because actions may modify the dicts they are passed
        return self._get_action(action)(dict(context), dict(data_dict))


class RemoteCKAN(object):
    """
    An interface to the the CKAN API actions on a remote CKAN instance.

    :param address: the web address of the CKAN instance, e.g.
                    'http://demo.ckan.org', stored as self.address
    :param apikey: the API key to pass as an 'X-CKAN-API-Key' header
                    when actions are called, stored as self.apikey
    :param request_fn: a callable that will be used to make requests

    The default implementation of request_fn is::

      def request_fn(url, data, headers):
          req = urllib2.Request(url, data, headers)
          try:
              r = urllib2.urlopen(req)
              return r.getcode(), r.read()
          except:
              return e.code, e.read()

    """
    def __init__(self, address, apikey=None, request_fn=None):
        self.address = address
        self.apikey = apikey
        self.action = ActionShortcut(self)
        if request_fn:
            self._request_fn = request_fn

    def call_action(self, action, data_dict=None, apikey=None):
        """
        :param action: the action name, e.g. 'package_create'
        :param data_dict: the dict to pass to the action as JSON,
                          defaults to {}

        This function parses the response from the server as JSON and
        returns the decoded value.  When an error is returned this
        function will convert it back to an exception that matches the
        one the action function itself raised.
        """
        url, data, headers = prepare_action(action, data_dict,
                                            apikey or self.apikey)
        status, response = self._request_fn(self.address + url, data, headers)
        return reverse_apicontroller_action(status, response)

    def _request_fn(self, url, data, headers):
        req = urllib2.Request(url, data, headers)
        try:
            r = urllib2.urlopen(req)
            return r.getcode(), r.read()
        except urllib2.HTTPError, e:
            return e.code, e.read()


class TestAppCKAN(object):
    """
    An interface to the the CKAN API actions on a paste TestApp

    :param test_app: the paste.fixture.TestApp instance, stored as
                    self.test_app
    :param apikey: the API key to pass as an 'X-CKAN-API-Key' header
                    when actions are called, stored as self.apikey
    """
    def __init__(self, test_app, apikey=None):
        self.test_app = test_app
        self.apikey = apikey
        self.action = ActionShortcut(self)

    def call_action(self, action, data_dict=None, apikey=None):
        """
        :param action: the action name, e.g. 'package_create'
        :param data_dict: the dict to pass to the action as JSON,
                          defaults to {}

        This function parses the response from the server as JSON and
        returns the decoded value.  When an error is returned this
        function will convert it back to an exception that matches the
        one the action function itself raised.
        """
        url, data, headers = prepare_action(action, data_dict,
                                            apikey or self.apikey)
        r = self.test_app.post(url, data, headers, expect_errors=True)
        return reverse_apicontroller_action(r.status, r.body)


def prepare_action(action, data_dict=None, apikey=None):
    """
    Return action_url, data_json, http_headers
    """
    if not data_dict:
        data_dict = {}
    data = json.dumps(data_dict)
    headers = {'Content-Type': 'application/json'}
    if apikey:
        apikey = str(apikey)
        headers['X-CKAN-API-Key'] = apikey
        headers['Authorization'] = apikey
    url = '/api/action/' + action
    return url, data, headers


def reverse_apicontroller_action(status, response):
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
    except ValueError:
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
    raise CKANAPIError(response, status)
