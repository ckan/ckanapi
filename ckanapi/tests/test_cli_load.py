from ckanapi.cli.load import load_things, load_things_worker
from ckanapi.errors import NotFound
from ckanapi.common import ActionShortcut
import json

try:
    import unittest2 as unittest
except ImportError:
    import unittest
from io import BytesIO

class MockCKAN(object):
    def __init__(self):
        self.action = ActionShortcut(self)

    def call_action(self, name, data_dict):
        try:
            return {
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
                'package_create': {
                    None: {'name': 'something-new'},
                    },
                }[name][data_dict.get('id')]
        except KeyError:
            raise NotFound()


class TestCLILoad(unittest.TestCase):
    def setUp(self):
        self.ckan = MockCKAN()
        self.stdout = BytesIO()
        self.stderr = BytesIO()

    def test_create_one(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': False,
                },
            stdin=BytesIO(b'{"name": "45","title":"Forty-five"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, 'something-new')

