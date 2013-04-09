import urllib2
import json

class CKANAPIError(Exception):
    pass

try:
    from ckan.lib.navl.dictization_functions import DataError
    from ckan.logic import (ParameterError, NotAuthorized, NotFound,
                            ValidationError)
    from ckan.search import SearchQueryError, SearchError

except ImportError:
    # Implement the minimum to be compatible with existing errors
    # without requiring CKAN

    class DataError(CKANAPIError):
        def __init__(self, error):
            self.error = error

    class NotAuthorized(CKANAPIError):
        pass

    class NotFound(CKANAPIError):
        pass

    class ValidationError(CKANAPIError):
        def __init__(self, error_dict):
            self.error_dict = error_dict

    class ParameterError(CKANAPIError):
        pass

    class SearchQueryError(CKANAPIError):
        pass

    class SearchError(CKANAPIError):
        pass


class LocalCKAN(object):
    def __init__(self, username=None, context=None):
        from ckan.logic import get_action
        self._get_action = get_action

        if not username:
            username = self.get_site_username()
        self.username = username
        self.context = context

    def get_site_username(self):
        user = self._get_action('get_site_user')({'ignore_auth': True}, ())
        return user['name']

    def call_action(self, action, data_dict=None):
        if not data_dict:
            data_dict = []
        # copy dicts because actions may modify the dicts they are passed
        return self._get_action(action)(dict(self.context), dict(data_dict))


class RemoteCKAN(object):
    def __init__(self, address, api_key=None):
        self.address = address
        self.api_key = api_key

    def call_action(self, action, data_dict=None):
        if not data_dict:
            data_dict = {}
        data = json.dumps(data_dict)
        header = {'Content-Type': 'application/json'}
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
        err = parsed.get('error', {})
    except ValueError:
        err = {}

    etype = err.get('__type')
    emessage = err.get('message', ': ').split(': ', 1)[1]
    if etype == 'Search Query Error':
        # I refuse to eval(emessage), even if it would be more correct
        raise SearchQueryError(emessage) 
    elif etype == 'Search Error':
        # I refuse to eval(emessage), even if it would be more correct
        raise SearchError(emessage) 
    elif etype == 'Parameter Error':
        e = ParameterError()
        e.extra_msg = emessage
        raise e
    elif etype == 'Validation Error':
        raise ValidationError(err)
    elif etype == 'Not Found Error':
        e = NotFound()
        e.extra_msg = emessage
        raise e
    elif etype == 'Not Found Error':
        raise NotAuthorized()
    elif status == 400:
        raise DataError(response.split(': ')[-1].split(' - ', 1)[0])

    # don't recognize the error
    raise CKANAPIError(response, status)
