import urllib2
import json

class CKANAPIError(Exception):
    def __str__(self):
        return repr(self.args)

try:
    from ckan.logic import (ParameterError, NotAuthorized, NotFound,
                            ValidationError)
    from ckan.lib.search import SearchQueryError, SearchError

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

    class ParameterError(CKANAPIError):
        def __init__(self, extra_msg):
            self.extra_msg = extra_msg
        def __str__(self):
            return self.extra_msg

    class SearchQueryError(CKANAPIError):
        pass

    class SearchError(CKANAPIError):
        pass


class ActionShortcut(object):
    def __init__(self, ckan):
        self._ckan = ckan

    def __getattr__(self, name):
        def action(**kwargs):
            return self._ckan.call_action(name, kwargs)
        return action


class LocalCKAN(object):
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

    def call_action(self, action, data_dict=None, context=None):
        if not data_dict:
            data_dict = []
        if context is None:
            context = self.context
        # copy dicts because actions may modify the dicts they are passed
        return self._get_action(action)(dict(context), dict(data_dict))


class RemoteCKAN(object):
    def __init__(self, address, api_key=None):
        self.address = address
        self.api_key = api_key
        self.action = ActionShortcut(self)

    def call_action(self, action, data_dict=None):
        if not data_dict:
            data_dict = {}
        data = json.dumps(data_dict)
        header = {'Content-Type': 'application/json'}
        if self.api_key:
            header['Authorization'] = self.api_key
        url = self.address + '/api/action/' + action
        req = urllib2.Request(url, data, headers=header)
        try:
            r = urllib2.urlopen(req)
            status = r.getcode()
            response = r.read()
        except urllib2.HTTPError, e:
            status = e.code
            response = e.read()
        return reverse_apicontroller_action(response, status)


def reverse_apicontroller_action(response, status):
    """
    Make an API call look like a direct action call by reversing the
    exception -> HTTP response translation that APIController.action does
    """
    try:
        parsed = json.loads(response)
        if status == 200:
            return parsed
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
    elif etype == 'Parameter Error':
        raise ParameterError(emessage)
    elif etype == 'Validation Error':
        raise ValidationError(err)
    elif etype == 'Not Found Error':
        raise NotFound(emessage)
    elif etype == 'Authorization Error':
        raise NotAuthorized()

    # don't recognize the error
    raise CKANAPIError(response, status)
