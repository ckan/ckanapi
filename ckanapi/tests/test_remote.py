import subprocess
import time
import os
import atexit
import socket
import requests

from ckanapi import RemoteCKAN, NotFound
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
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

TEST_CKAN = 'http://localhost:8901'

NUMBER_THING_CSV = """
Number,Thing
5,sasquach
""".lstrip()

class TestRemoteAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(os.path.dirname(__file__), 'mock/mock_ckan.py')
        _mock_ckan = subprocess.Popen(['python2', script],
            stdout=DEVNULL, stderr=DEVNULL)
        def kill_child():
            try:
                _mock_ckan.kill()
                _mock_ckan.wait()
            except OSError:
                pass  # alread cleaned up from tearDownClass
        atexit.register(kill_child)
        cls._mock_ckan = _mock_ckan
        while True: # wait for the server to start
            try:
                r = urlopen(TEST_CKAN + '/api/action/site_read')
                if r.getcode() == 200:
                    break
            except URLError as e:
                pass
            time.sleep(0.1)

    def test_good_oldstyle(self):
        ckan = RemoteCKAN(TEST_CKAN)
        self.assertEqual(
            ckan.action.organization_list(),
            ['aa', 'bb', 'cc'])
        ckan.close()

    def test_good(self):
        with RemoteCKAN(TEST_CKAN) as ckan:
            self.assertEqual(
                ckan.action.organization_list(),
                ['aa', 'bb', 'cc'])

    def test_missing(self):
        with RemoteCKAN(TEST_CKAN) as ckan:
            self.assertRaises(
                NotFound,
                ckan.action.organization_show,
                id='qqq')

    def test_default_ua(self):
        with RemoteCKAN(TEST_CKAN) as ckan:
            self.assertTrue(
                ckan.action.test_echo_user_agent().startswith('ckanapi'))

    def test_custom_ua(self):
        ua = 'testckanapibot/1.0 (+https://github.com/ckan/ckanapi)'
        with RemoteCKAN(TEST_CKAN, user_agent=ua) as ckan:
            self.assertEqual(ckan.action.test_echo_user_agent(), ua)

    def test_default_content_type(self):
        with RemoteCKAN(TEST_CKAN) as ckan:
            self.assertEqual(ckan.action.test_echo_content_type(),
                "application/json")

    def test_resource_upload(self):
        with RemoteCKAN(TEST_CKAN) as ckan:
            res = ckan.call_action('test_upload',
                {'option': "42"},
                files={'upload': StringIO(NUMBER_THING_CSV)})
        self.assertEqual(res.get('last_row'), ['5', 'sasquach'])

    def test_resource_upload_extra_param(self):
        with RemoteCKAN(TEST_CKAN) as ckan:
            res = ckan.call_action('test_upload',
                {'option': "42"},
                files={'upload': StringIO(NUMBER_THING_CSV)})
        self.assertEqual(res.get('option'), "42")

    def test_resource_upload_unicode_param(self):
        uname = b't\xc3\xab\xc3\x9ft resource'.decode('utf-8')
        with RemoteCKAN(TEST_CKAN) as ckan:
            res = ckan.call_action('test_upload',
                {'option': uname},
                files={'upload': StringIO(NUMBER_THING_CSV)})
        self.assertEqual(res.get('option'), uname)

    def test_resource_upload_content_type(self):
        with RemoteCKAN(TEST_CKAN) as ckan:
            res = ckan.call_action('test_echo_content_type',
                {'option': "42"},
                files={'upload': StringIO(NUMBER_THING_CSV)})
        self.assertEqual(res.split(';')[0], "multipart/form-data")

    @classmethod
    def tearDownClass(cls):
        cls._mock_ckan.kill()
        cls._mock_ckan.wait()

