import subprocess
import time
import os

import ckanapi
try:
    import unittest2 as unittest
except ImportError:
    import unittest
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')
try:
    from urllib2 import urlopen, URLError
except ImportError:
    from urllib.request import urlopen, URLError


class TestRemoteAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(os.path.dirname(__file__), 'mock/mock_ckan.py')
        cls._mock_ckan = subprocess.Popen(['python', script],
            stdout=DEVNULL, stderr=DEVNULL)
        while True: # wait for the server to start
            try:
                urlopen('http://localhost:8901')
            except URLError as e:
                if hasattr(e, 'getcode') and e.getcode() == 404:
                    break
            time.sleep(0.1)

    def setUp(self):
        self.ckan = ckanapi.RemoteCKAN('http://localhost:8901')

    def test_good(self):
        self.assertEqual(
            self.ckan.action.organization_list(),
            ['aa', 'bb', 'cc'])

    def test_missing(self):
        self.assertRaises(
            ckanapi.NotFound,
            self.ckan.action.organization_show,
            id='qqq')

    def test_default_ua(self):
        self.assertTrue(
            self.ckan.action.test_echo_user_agent().startswith('ckanapi'))

    def test_custom_ua(self):
        ua = 'testckanapibot/1.0 (+https://github.com/open-data/ckanapi)'
        ckan = ckanapi.RemoteCKAN('http://localhost:8901', user_agent=ua)

        self.assertEqual(ckan.action.test_echo_user_agent(), ua)

    def test_resource_upload(self):
        res = self.ckan.call_action('test_upload',
            {'package_id': "42"},
            files=[('upload', open(
                os.path.join(os.path.dirname(__file__), 'sample.csv'), 'rb'))])
        self.assertEqual(res, {'last_row': ['5', 'sasquach']})

    @classmethod
    def tearDownClass(cls):
        cls._mock_ckan.kill()
        cls._mock_ckan.wait()

