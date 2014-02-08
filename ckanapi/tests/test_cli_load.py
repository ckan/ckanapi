from ckanapi.cli.load import load_things, load_things_worker
from ckanapi.errors import NotFound, ValidationError, NotAuthorized
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
        if name == 'package_show' and data_dict['id'] == 'seekrit':
            raise NotAuthorized('naughty user')
        if name == 'package_create' and data_dict['name'] == '34':
            raise ValidationError({'name': 'That URL is already in use.'})
        try:
            return {
                'package_show': {
                    '12': {'title': "Twelve"},
                    '30ish': {'id': '34', 'title': "Thirty-four"},
                    '34': {'id': '34', 'title': "Thirty-four"},
                    },
                'group_show': {
                    'ab': {'title': "ABBA"},
                    },
                'organization_show': {
                    'cd': {'id': 'cd', 'title': "Super Trouper"},
                    },
                'package_create': {
                    None: {'name': 'something-new'},
                    },
                'package_update': {
                    '34': {'name': 'something-updated'},
                    },
                'group_update': {
                    'ab': {'name': 'group-updated'},
                    },
                'organization_update': {
                    'cd': {'name': 'org-updated'},
                    },
                'organization_create': {
                    None: {'name': 'org-created'},
                    },
                }[name][data_dict.get('id')]
        except KeyError:
            raise NotFound()


class TestCLILoad(unittest.TestCase):
    def setUp(self):
        self.ckan = MockCKAN()
        self.stdout = BytesIO()
        self.stderr = BytesIO()

    def test_create(self):
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

    def test_create_only(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': True,
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

    def test_create_bad_option(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': True,
                },
            stdin=BytesIO(b'{"name": "45","title":"Forty-five"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'show')
        self.assertEqual(error, 'NotFound')
        self.assertEqual(data, [None, '45'])

    def test_update(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': False,
                },
            stdin=BytesIO(b'{"name": "30ish","title":"3.4 times ten"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, 'something-updated')

    def test_update_only(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': True,
                },
            stdin=BytesIO(b'{"name": "34","title":"3.4 times ten"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, 'something-updated')

    def test_update_bad_option(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': True,
                '--update-only': False,
                },
            stdin=BytesIO(b'{"name": "34","title":"3.4 times ten"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, 'ValidationError')
        self.assertEqual(data, {'name': 'That URL is already in use.'})

    def test_update_unauthorized(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': False,
                },
            stdin=BytesIO(b'{"name": "seekrit", "title": "Things"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'show')
        self.assertEqual(error, 'NotAuthorized')
        self.assertEqual(data, 'naughty user')

    def test_update_group(self):
        load_things_worker(self.ckan, 'groups', {
                '--create-only': False,
                '--update-only': False,
                },
            stdin=BytesIO(b'{"id": "ab","title":"a balloon"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, 'group-updated')

    def test_update_organization_two(self):
        load_things_worker(self.ckan, 'organizations', {
                '--create-only': False,
                '--update-only': False,
                },
            stdin=BytesIO(
                b'{"name": "cd", "title": "Go"}\n'
                b'{"name": "ef", "title": "Play"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response.count(b'\n'), 2, response)
        self.assertEqual(response[-1:], b'\n')
        r1, r2 = response.split(b'\n', 1)
        timstamp, action, error, data = json.loads(r1.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, 'org-updated')
        timstamp, action, error, data = json.loads(r2.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, 'org-created')


