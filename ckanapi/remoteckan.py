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

import requests


class RemoteCKAN(object):
    """
    An interface to the the CKAN API actions on a remote CKAN instance.

    :param address: the web address of the CKAN instance, e.g.
                    'http://demo.ckan.org', stored as self.address
    :param apikey: the API key to pass as an 'X-CKAN-API-Key' header
                    when actions are called, stored as self.apikey
    :param user_agent: the User-agent to report when making requests
    :param get_only: only use GET requests (default: False)
    :param session: session to use (default: None)
    """
    def __init__(self, address, apikey=None, user_agent=None, get_only=False, session=None):
        self.address = address
        self.apikey = apikey
        self.get_only = get_only
        self.session = session
        if not user_agent:
            user_agent = "ckanapi/{version} (+{url})".format(
                version=__version__,
                url='https://github.com/ckan/ckanapi')
        self.user_agent = user_agent
        self.action = ActionShortcut(self)

        net_loc = urlparse(address)
        if ']' in net_loc:
            net_loc = net_loc[:net_loc.index(']') + 1]
        elif ':' in net_loc:
            net_loc = net_loc[:net_loc.index(':')]
        if net_loc not in MY_SITES:
            # add your sites to MY_SITES above instead of removing this
            self.parallel_limit = PARALLEL_LIMIT

    def call_action(self, action, data_dict=None, context=None, apikey=None,
            files=None, requests_kwargs=None):
        """
        :param action: the action name, e.g. 'package_create'
        :param data_dict: the dict to pass to the action as JSON,
                          defaults to {}
        :param context: always set to None for RemoteCKAN
        :param apikey: API key for authentication
        :param files: None or {field-name: file-to-be-sent, ...}
        :param requests_kwargs: kwargs for requests get/post calls

        This function parses the response from the server as JSON and
        returns the decoded value.  When an error is returned this
        function will convert it back to an exception that matches the
        one the action function itself raised.
        """
        if context:
            raise CKANAPIError("RemoteCKAN.call_action does not support "
                "use of context parameter, use apikey instead")
        if files and self.get_only:
            raise CKANAPIError("RemoteCKAN: files may not be sent when "
                "get_only is True")
        url, data, headers = prepare_action(
            action, data_dict, apikey or self.apikey, files)
        headers['User-Agent'] = self.user_agent
        url = self.address.rstrip('/') + '/' + url
        requests_kwargs = requests_kwargs or {}
        if not self.session:
            self.session = requests.Session()
        if self.get_only:
            status, response = self._request_fn_get(url, data_dict, headers, requests_kwargs)
        else:
            status, response = self._request_fn(url, data, headers, files, requests_kwargs)
        return reverse_apicontroller_action(url, status, response)

    def _request_fn(self, url, data, headers, files, requests_kwargs):
        r = self.session.post(url, data=data, headers=headers, files=files,
            allow_redirects=False, **requests_kwargs)
        # allow_redirects=False because: if a post is redirected (e.g. 301 due
        # to a http to https redirect), then the second request is made to the
        # new URL, but *without* the data. This gives a confusing "No request
        # body data" error. It is better to just return the 301 to the user, so
        # we disallow redirects.
        return r.status_code, r.text

    def _request_fn_get(self, url, data_dict, headers, requests_kwargs):
        r = self.session.get(url, params=data_dict, headers=headers,
            **requests_kwargs)
        return r.status_code, r.text

    def close(self):
        """Close session"""
        if self.session:
            self.session.close()
            self.session = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
