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


class TestRemoteAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(os.path.dirname(__file__), 'mock/mock_ckan.py')
        cls._mock_ckan = subprocess.Popen(['python', script], stdout=DEVNULL)
        time.sleep(0.25) # give the server a chance to start

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

    @classmethod
    def tearDownClass(cls):
        cls._mock_ckan.kill()

