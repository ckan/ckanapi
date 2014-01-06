import urllib
try:
    import urllib2
except ImportError: # python3
    urllib2 = urllib

from ckanapi.errors import CKANAPIError
from ckanapi.common import (ActionShortcut, prepare_action,
    reverse_apicontroller_action)

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

    def call_action(self, action, data_dict=None, context=None, apikey=None):
        """
        :param action: the action name, e.g. 'package_create'
        :param data_dict: the dict to pass to the action as JSON,
                          defaults to {}

        This function parses the response from the server as JSON and
        returns the decoded value.  When an error is returned this
        function will convert it back to an exception that matches the
        one the action function itself raised.
        """
        if context:
            raise CKANAPIError("RemoteCKAN.call_action does not support "
                "use of context parameter, use apikey instead")
        url, data, headers = prepare_action(action, data_dict,
                                            apikey or self.apikey)
        url = urllib.basejoin(self.address, url)
        status, response = self._request_fn(url, data, headers)
        return reverse_apicontroller_action(url, status, response)

    def _request_fn(self, url, data, headers):
        req = urllib2.Request(url, data, headers)
        try:
            r = urllib2.urlopen(req)
            return r.getcode(), r.read()
        except urllib2.HTTPError as e:
            return e.code, e.read()


