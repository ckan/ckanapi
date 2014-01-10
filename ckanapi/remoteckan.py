try:
    from urllib2 import Request, urlopen, HTTPError
    from urlparse import urlparse
except ImportError:
    from urllib.request import Request, urlopen, HTTPError
    from urllib.parse import urlparse

from ckanapi.errors import CKANAPIError
from ckanapi.common import (ActionShortcut, prepare_action,
    reverse_apicontroller_action)
from ckanapi.version import __version__

# add your sites here to remove parallel limits on ckanapi cli
MY_SITES = ['localhost', '127.0.0.1', '[::1]']

# add your site above instead of changing this
PARALLEL_LIMIT = 3


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
          req = Request(url, data, headers)
          try:
              r = urlopen(req)
              return r.getcode(), r.read()
          except:
              return e.code, e.read()

    """
    def __init__(self, address, apikey=None, request_fn=None, user_agent=None):
        self.address = address
        self.apikey = apikey
        if not user_agent:
            user_agent = "ckanapi/{version} (+{url})".format(
                version=__version__,
                url='https://github.com/open-data/ckanapi')
        self.user_agent = user_agent
        self.action = ActionShortcut(self)
        if request_fn:
            self._request_fn = request_fn

        net_loc = urlparse(address)
        if ']' in net_loc:
            net_loc = net_loc[:net_loc.index(']') + 1]
        elif ':' in net_loc:
            net_loc = net_loc[:net_loc.index(':')]
        if net_loc not in MY_SITES:
            # add your sites to MY_SITES above instead of removing this
            self.parallel_limit = PARALLEL_LIMIT

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
        headers['User-Agent'] = self.user_agent
        url = self.address.rstrip('/') + '/' + url
        status, response = self._request_fn(url, data, headers)
        return reverse_apicontroller_action(url, status, response)

    def _request_fn(self, url, data, headers):
        req = Request(url, data, headers)
        try:
            r = urlopen(req)
            return r.getcode(), r.read()
        except HTTPError as e:
            return e.code, e.read()


