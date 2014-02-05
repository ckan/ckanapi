from ckanapi.cli.dump import dump_things, dump_things_worker
from ckanapi.errors import NotFound
from ckanapi.common import ActionShortcut
import json

try:
    import unittest2 as unittest
except ImportError:
    import unittest
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

class MockCKAN(object):
    def __init__(self):
        self.action = ActionShortcut(self)

    def call_action(self, name, data_dict):
        try:
            return {
                'package_list': {
                    None: ['12', '34']
                    },
                'package_show': {
                    '12': {'title': "Twelve"},
                    '34': {'title': "Thirty-four"},
                    },
                'group_show': {
                    'ab': {'title': "ABBA"},
                    },
                'organization_show': {
                    'cd': {'title': "Super Trouper"},
                    },
                }[name][data_dict.get('id')]
        except KeyError:
            raise NotFound()


class TestCLIDump(unittest.TestCase):
    def setUp(self):
        self.ckan = MockCKAN()
        self.stdout = StringIO()

    def test_worker_one(self):
        rval = dump_things_worker(self.ckan, 'datasets', {},
            stdin=StringIO(b'"34"\n'), stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1], b'\n')
        timstamp, error, data = json.loads(response)
        self.assertEqual(error, None)
        self.assertEqual(data, {"title":"Thirty-four"})

    def test_worker_two(self):
        rval = dump_things_worker(self.ckan, 'datasets', {},
            stdin=StringIO(b'"12"\n"34"\n'), stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response.count(b'\n'), 2, response)
        self.assertEqual(response[-1], b'\n')
        r1, r2 = response.split('\n', 1)
        timstamp, error, data = json.loads(r1)
        self.assertEqual(error, None)
        self.assertEqual(data, {"title":"Twelve"})
        timstamp, error, data = json.loads(r2)
        self.assertEqual(error, None)
        self.assertEqual(data, {"title":"Thirty-four"})

    def test_worker_error(self):
        dump_things_worker(self.ckan, 'datasets', {},
            stdin=StringIO(b'"99"\n'), stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1], b'\n')
        timstamp, error, data = json.loads(response)
        self.assertEqual(error, "NotFound")
        self.assertEqual(data, None)

    def test_worker_group(self):
        dump_things_worker(self.ckan, 'groups', {},
            stdin=StringIO(b'"ab"\n'), stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1], b'\n')
        timstamp, error, data = json.loads(response)
        self.assertEqual(error, None)
        self.assertEqual(data, {"title":"ABBA"})

    def test_worker_organization(self):
        dump_things_worker(self.ckan, 'organizations', {},
            stdin=StringIO(b'"cd"\n'), stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1], b'\n')
        timstamp, error, data = json.loads(response)
        self.assertEqual(error, None)
        self.assertEqual(data, {"title":"Super Trouper"})

