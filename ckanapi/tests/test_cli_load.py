from ckanapi.cli.load import load_things, load_things_worker
from ckanapi.errors import NotFound, ValidationError, NotAuthorized
import json

import unittest
from io import BytesIO

class MockCKAN(object):
    def call_action(self, name, data_dict, requests_kwargs=None):
        if name == 'package_show' and data_dict['id'] == 'seekrit':
            raise NotAuthorized('naughty user')
        if name == 'package_create' and data_dict.get('name') == '34':
            raise ValidationError({'name': 'That URL is already in use.'})
        if name == 'organization_update':
            if data_dict['id'] == 'used' and data_dict.get('users') != [
                    {"capacity": "editor", "name": "test-user"}]:
                raise ValidationError({'users': 'should be unchanged'})
            if data_dict['id'] == 'unused' and data_dict.get('users') != []:
                raise ValidationError({'users': 'should be cleared'})
        if name == 'resource_view_show' and data_dict['id'] == '123':
            raise NotFound('no resource view with ID 123')
        if name == 'datastore_search' and (data_dict['resource_id'] == '123' or data_dict['resource_id'] == '111'):
            raise NotFound('no resource datastore with ID 123')
        if name == 'datastore_create' and (data_dict['resource_id'] == '789' or data_dict['resource_id'] == '111'):
            raise ValidationError({'pg_error': 'no db connection'})
        try:
            return {
                'package_show': {
                    '12': {'title': "Twelve"},
                    '30ish': {'id': '34', 'title': "Thirty-four"},
                    '34': {'id': '34', 'title': "Thirty-four"},
                    '46': {'id': '46', 'name': '46', 'title': 'Forty-six'},
                },
                'group_show': {
                    'ab': {'title': "ABBA"},
                },
                'organization_show': {
                    'cd': {'id': 'cd', 'title': "Super Trouper"},
                    'used': {'users': [{"capacity": "editor", "name": "test-user"}]},
                    'unused': {'users': [{"capacity": "editor", "name": "test-user"}]},
                    'mems': {'id': 'mems', 'name': 'mems',
                             "users": [{"capacity": "admin", "name": "test-user-admin"},
                                       {"capacity": "editor", "name": "test-user"}]},
                },
                'package_create': {
                    None: {'id': 'some-generated-uuid', 'name': 'something-new'},
                    '46': {'id': '46', 'name': '46'},
                },
                'package_update': {
                    '34': {'id': '34', 'name': 'something-updated'},
                    '46': {'id': '46', 'name': '46'},
                },
                'resource_view_show': {
                    '456': {'description': 'Test view', 'package_id': '46', 'resource_id': '456'}
                },
                'resource_view_create': {
                    '123': {'description': 'Test view', 'package_id': '46', 'resource_id': '123'},
                },
                'resource_view_update': {
                    '456': {'description': 'Test view', 'package_id': '46', 'resource_id': '456'},
                },
                'datastore_search': {
                    '456': {'resource_id': '456', 'fields': [{'id': 'test_field1', 'type': 'text'}, {'id': 'test_field2', 'type': 'text'}]},
                    '789': {'resource_id': '789', 'fields': [{'id': 'test_field1', 'type': 'text'}, {'id': 'test_field2', 'type': 'text'}]},
                },
                'datastore_create': {
                    '123': {'resource_id': '123', 'fields': [{'id': 'test_field1', 'type': 'text'}, {'id': 'test_field2', 'type': 'text'}]},
                    '456': {'resource_id': '456', 'fields': [{'id': 'test_field1', 'type': 'text'}, {'id': 'test_field2', 'type': 'text'}]},
                },
                'group_update': {
                    'ab': {'id': 'ab', 'name': 'group-updated'},
                },
                'organization_update': {
                    'cd': {'id': 'cd', 'name': 'org-updated'},
                    'used': {'id': 'used', 'name': 'users-unchanged'},
                    'unused': {'id': 'unused', 'name': 'users-cleared'},
                    'mems': {'id': 'mems', 'name': 'mems', "users": [{"capacity": "admin", "name": "test-user-admin"}]},
                },
                'organization_create': {
                    None: {'id': 'some-generated-uuid', 'name': 'org-created'},
                    'mems': {'id': 'mems', 'name': 'mems', "users": [{"capacity": "editor", "name": "test-user"}]},
                },
                'organization_member_create': {
                    'mems': {'id': 'mems', 'role': 'admin', 'username': 'test-user-admin'}
                },
                'user_show': {
                    'test_user': {'id': 'test_user', 'name': 'test_user'},
                },
                'user_create': {
                    None: {'id': 'some-generated-uuid', 'name': 'test_user'}
                },
                'api_token_create': {
                    'this-is-a-token': {
                        'id': 'this-is-a-token'
                    }
                },
                }[name][data_dict.get('id', data_dict.get('resource_id'))]
        except KeyError as e:
            raise NotFound()


class TestCLILoad(unittest.TestCase):
    def setUp(self):
        self.ckan = MockCKAN()
        self.stdout = BytesIO()
        self.stderr = BytesIO()

    def test_create_with_no_resources(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{"name": "45","title":"Forty-five"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'some-generated-uuid', 'name': 'something-new'})

    def test_create_with_corrupted_resources(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{"name": "45","title":"Forty-five","resources":[{"id":"123"}]}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'some-generated-uuid', 'name': 'something-new'})

    def test_create_with_complete_resources(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(
                 b'{"name": "45","title":"Forty-five",'
                 b'"resources":[{"id":"123","url_type":"","url":"http://example.com"}]}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'some-generated-uuid', 'name': 'something-new'})

    def test_create_with_resource_views(self):
        """
        A dataset with Resources that have views should create
        the resource views.
        """
        payload = {
            'name': '46',
            'title': 'Forty-six',
            'resources': [{
                'name': 'resource1',
                'format': 'csv',
                'id': '123',
                'url': 'http://example.com',
                'datastore_active': True,
                'resource_views': [{
                    'description': 'Test view',
                    'filterable': True,
                    'id': '123',
                    'resource_id': '123',
                    'responsive': True,
                    'show_fields': ['_id']
                }]
            }]
        }
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': True,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': True,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(json.dumps(payload).encode()),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'some-generated-uuid', 'name': 'something-new', 'created_resource_views': ['123']})

    def test_create_with_resource_datastore_fields(self):
        """
        A dataset with Resources that have datastore fields should create
        the datastore table with the fields.
        """
        payload = {
            'name': '46',
            'title': 'Forty-six',
            'resources': [{
                'name': 'resource1',
                'format': 'csv',
                'id': '123',
                'url': 'http://example.com',
                'datastore_active': True,
                'datastore_fields': [
                    {'id': 'test_field1', 'type': 'text'},
                    {'id': 'test_field2', 'type': 'text'},
                ]
            }]
        }
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': True,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': True,
                '--append-users': False,
                },
            stdin=BytesIO(json.dumps(payload).encode()),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'some-generated-uuid', 'name': 'something-new', 'created_datastore_tables': ['123']})

    def test_create_with_bad_resource_datastore_fields(self):
        """
        A dataset with Resources that have datastore fields that exist
        but throw ValidationErrors should skip them.
        """
        payload = {
            'name': '46',
            'title': 'Forty-six',
            'resources': [{
                'name': 'resource1',
                'format': 'csv',
                'id': '789',
                'url': 'http://example.com',
                'datastore_active': True,
                'datastore_fields': [
                    {'id': 'test_field1', 'type': 'text'},
                    {'id': 'test_field2', 'type': 'text'},
                ]
            }]
        }
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': True,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': True,
                '--append-users': False,
                },
            stdin=BytesIO(json.dumps(payload).encode()),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'some-generated-uuid', 'name': 'something-new', 'skipped_datastore_tables': ["789: {'pg_error': 'no db connection'}"]})

    def test_create_only(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': True,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{"name": "45","title":"Forty-five"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'some-generated-uuid', 'name': 'something-new'})

    def test_create_empty_dict(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'some-generated-uuid', 'name': 'something-new'})

    def test_create_bad_option(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': True,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{"name": "45","title":"Forty-five"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'show')
        self.assertEqual(error, 'NotFound')
        self.assertEqual(data, [None, '45'])

    def test_update_with_no_resources(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{"name": "30ish","title":"3.4 times ten"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': '34', 'name': 'something-updated'})

    def test_update_with_corrupted_resources(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{"name": "30ish","title":"3.4 times ten","resources":[{"id":"123"}]}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': '34', 'name': 'something-updated'})

    def test_update_with_complete_resources(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(
                 b'{"name": "30ish","title":"3.4 times ten",'
                 b'"resources":[{"id":"123","url_type":"","url":"http://example.com"}]}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': '34', 'name': 'something-updated'})

    def test_update_with_resource_views(self):
        """
        A dataset with Resources that have views should update
        the resource views.
        """
        payload = {
            'name': '46',
            'title': 'Forty-six',
            'resources': [{
                'name': 'resource1',
                'format': 'csv',
                'id': '456',
                'url': 'http://example.com',
                'datastore_active': True,
                'resource_views': [{
                    'description': 'Test view',
                    'filterable': True,
                    'id': '456',
                    'resource_id': '456',
                    'responsive': True,
                    'show_fields': ['_id']
                }]
            }]
        }
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': True,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': True,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(json.dumps(payload).encode()),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': '46', 'name': '46', 'updated_resource_views': ['456']})

    def test_update_with_new_resource_views(self):
        """
        A dataset with Resources that have NEW views should not
        be able to create the resource views, just skip them.
        """
        payload = {
            'name': '46',
            'title': 'Forty-six',
            'resources': [{
                'name': 'resource1',
                'format': 'csv',
                'id': '456',
                'url': 'http://example.com',
                'datastore_active': True,
                'resource_views': [{
                    'description': 'Test view',
                    'filterable': True,
                    'id': '123',
                    'resource_id': '456',
                    'responsive': True,
                    'show_fields': ['_id']
                }]
            }]
        }
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': True,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': True,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(json.dumps(payload).encode()),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': '46', 'name': '46', 'skipped_resource_views': ['123']})

    def test_update_with_resource_datastore_fields(self):
        """
        A dataset with Resources that have datastore fields should create
        the datastore table with the fields.
        """
        payload = {
            'name': '46',
            'title': 'Forty-six',
            'resources': [{
                'name': 'resource1',
                'format': 'csv',
                'id': '456',
                'url': 'http://example.com',
                'datastore_active': True,
                'datastore_fields': [
                    {'id': 'test_field1', 'type': 'text'},
                    {'id': 'test_field2', 'type': 'text'},
                ]
            }]
        }
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': True,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': True,
                '--append-users': False,
                },
            stdin=BytesIO(json.dumps(payload).encode()),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': '46', 'name': '46', 'created_datastore_tables': ['456']})

    def test_update_with_bad_resource_datastore_fields(self):
        """
        A dataset with Resources that have datastore fields that do not exist
        should throw ValidationErrors should raise the error as normal.
        """
        payload = {
            'name': '46',
            'title': 'Forty-six',
            'resources': [{
                'name': 'resource1',
                'format': 'csv',
                'id': '111',
                'url': 'http://example.com',
                'datastore_active': True,
                'datastore_fields': [
                    {'id': 'test_field1', 'type': 'text'},
                    {'id': 'test_field2', 'type': 'text'},
                ]
            }]
        }
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': True,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': True,
                '--append-users': False,
                },
            stdin=BytesIO(json.dumps(payload).encode()),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, 'ValidationError')
        self.assertEqual(data, {'pg_error': 'no db connection'})

    def test_update_with_resource_datastore_fields_no_resource_id(self):
        """
        A dataset with Resources that have datastore fields but no ID
        should raise a KeyError.
        """
        payload = {
            'name': '46',
            'title': 'Forty-six',
            'resources': [{
                'name': 'resource1',
                'format': 'csv',
                'url': 'http://example.com',
                'datastore_active': True,
                'datastore_fields': [
                    {'id': 'test_field1', 'type': 'text'},
                    {'id': 'test_field2', 'type': 'text'},
                ]
            }]
        }
        with self.assertRaises(KeyError) as ke:
            load_things_worker(self.ckan, 'datasets', {
                    '--create-only': False,
                    '--update-only': True,
                    '--upload-resources': False,
                    '--insecure': False,
                    '--resource-views': False,
                    '--datastore-fields': True,
                    '--append-users': False,
                    },
                stdin=BytesIO(json.dumps(payload).encode()),
                stdout=self.stdout)
        self.assertEqual(str(ke.exception), "'id'")

    def test_update_with_resource_views_no_resource_id(self):
        """
        A dataset with Resources that have views but no ID
        should raise a KeyError.
        """
        payload = {
            'name': '46',
            'title': 'Forty-six',
            'resources': [{
                'name': 'resource1',
                'format': 'csv',
                'url': 'http://example.com',
                'datastore_active': True,
                'resource_views': [{
                    'description': 'Test view',
                    'filterable': True,
                    'id': '123',
                    'resource_id': '456',
                    'responsive': True,
                    'show_fields': ['_id']
                }]
            }]
        }
        with self.assertRaises(KeyError) as ke:
            load_things_worker(self.ckan, 'datasets', {
                    '--create-only': False,
                    '--update-only': True,
                    '--upload-resources': False,
                    '--insecure': False,
                    '--resource-views': True,
                    '--datastore-fields': False,
                    '--append-users': False,
                    },
                stdin=BytesIO(json.dumps(payload).encode()),
                stdout=self.stdout)
        self.assertEqual(str(ke.exception), "'id'")

    def test_update_only(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': False,
                '--update-only': True,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{"name": "34","title":"3.4 times ten"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': '34', 'name': 'something-updated'})

    def test_update_bad_option(self):
        load_things_worker(self.ckan, 'datasets', {
                '--create-only': True,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
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
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
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
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{"id": "ab","title":"a balloon"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'ab', 'name': 'group-updated'})

    def test_update_organization_two(self):
        load_things_worker(self.ckan, 'organizations', {
                '--create-only': False,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
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
        self.assertEqual(data, {'id': 'cd', 'name': 'org-updated'})
        timstamp, action, error, data = json.loads(r2.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'some-generated-uuid', 'name': 'org-created'})

    def test_update_organization_with_users_unchanged(self):
        load_things_worker(self.ckan, 'organizations', {
                '--create-only': False,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{"id": "used", "title": "here"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'used', 'name': 'users-unchanged'})

    def test_update_organization_with_users_cleared(self):
        load_things_worker(self.ckan, 'organizations', {
                '--create-only': False,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{"id": "unused", "users": []}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'unused', 'name': 'users-cleared'})

    def test_update_organization_with_users_appended(self):
        load_things_worker(self.ckan, 'organizations', {
                '--create-only': True,
                '--update-only': False,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
                },
            stdin=BytesIO(b'{"id": "mems", "name": "mems", "users": [{"capacity": "editor", "name": "test-user"}]}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'mems', 'name': 'mems', "set_members": ["test-user[editor]"]})

        self.stdout.seek(0)
        self.stdout.truncate(0)

        load_things_worker(self.ckan, 'organizations', {
                '--create-only': False,
                '--update-only': True,
                '--upload-resources': False,
                '--insecure': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': True,
                },
            stdin=BytesIO(b'{"id": "mems", "name": "mems", "users": [{"capacity": "admin", "name": "test-user-admin"}]}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')

        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'update')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'mems', 'name': 'mems', "set_members": ["test-user-admin[admin]"]})

    def test_parent_load_two(self):
        load_things(self.ckan, 'datasets', {
                '--quiet': False,
                '--ckan-user': None,
                '--config': None,
                '--remote': None,
                '--apikey': None,
                '--worker': False,
                '--log': None,
                '--gzip': False,
                '--processes': '1',
                '--input': None,
                '--create-only': False,
                '--update-only': False,
                '--start-record': '1',
                '--max-records': None,
                '--upload-resources': False,
                '--upload-logo': False,
                '--insecure': False,
                '--api-tokens': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
            },
            worker_pool=self._mock_worker_pool,
            stdin=BytesIO(
                b'{"name": "cd", "title": "Go"}\n'
                b'{"name": "ef", "title": "Play"}\n'
                ),
            stdout=self.stdout,
            stderr=self.stderr)
        self.assertEqual(self.worker_cmd, [
            'ckanapi', 'load', 'datasets', '--worker'])
        self.assertEqual(self.worker_processes, 1)
        self.assertEqual(self.worker_jobs, [
            (1, b'{"name": "cd", "title": "Go"}\n'),
            (2, b'{"name": "ef", "title": "Play"}\n'),
            ])

    def test_parent_load_start_max(self):
        load_things(self.ckan, 'groups', {
                '--quiet': False,
                '--ckan-user': None,
                '--config': None,
                '--remote': None,
                '--apikey': None,
                '--worker': False,
                '--log': None,
                '--gzip': False,
                '--processes': '1',
                '--input': None,
                '--create-only': False,
                '--update-only': False,
                '--start-record': '2',
                '--max-records': '2',
                '--upload-resources': False,
                '--upload-logo': False,
                '--insecure': False,
                '--api-tokens': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
            },
            worker_pool=self._mock_worker_pool,
            stdin=BytesIO(
                b'{"name": "cd", "title": "Go"}\n'
                b'{"name": "ef", "title": "Play"}\n'
                b'{"name": "gh", "title": "Hotel"}\n'
                b'{"name": "ij", "title": "Ambient"}\n'
                ),
            stdout=self.stdout,
            stderr=self.stderr)
        self.assertEqual(self.worker_cmd, [
            'ckanapi', 'load', 'groups', '--worker'])
        self.assertEqual(self.worker_processes, 1)
        self.assertEqual(self.worker_jobs, [
            (2, b'{"name": "ef", "title": "Play"}\n'),
            (3, b'{"name": "gh", "title": "Hotel"}\n'),
            ])

    def test_parent_parallel_limit(self):
        self.ckan.parallel_limit = 2
        load_things(self.ckan, 'datasets', {
                '--quiet': False,
                '--ckan-user': None,
                '--config': None,
                '--remote': None,
                '--apikey': None,
                '--worker': False,
                '--log': None,
                '--gzip': False,
                '--processes': '5',
                '--input': None,
                '--create-only': False,
                '--update-only': False,
                '--start-record': '1',
                '--max-records': None,
                '--upload-resources': False,
                '--upload-logo': False,
                '--insecure': False,
                '--api-tokens': False,
                '--resource-views': False,
                '--datastore-fields': False,
                '--append-users': False,
            },
            worker_pool=self._mock_worker_pool,
            stdin=BytesIO(
                b'{"name": "cd", "title": "Go"}\n'
                b'{"name": "ef", "title": "Play"}\n'
                ),
            stdout=self.stdout,
            stderr=self.stderr)
        self.assertEqual(self.worker_cmd, [
            'ckanapi', 'load', 'datasets', '--worker'])
        self.assertEqual(self.worker_processes, 2)

    def test_create_user(self):
        load_things_worker(self.ckan, 'users', {
                '--create-only': True,
                '--update-only': False,
                '--insecure': False,
                '--api-tokens': False,
                },
            stdin=BytesIO(b'{"name":"test_user"}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'id': 'some-generated-uuid', 'name': 'test_user'})

    def test_create_user_with_api_token(self):
        load_things_worker(self.ckan, 'users', {
                '--create-only': True,
                '--update-only': False,
                '--insecure': False,
                '--api-tokens': True,
                },
            stdin=BytesIO(b'{"name":"test_user","api_token_list":[{"user_id":"test_user","id":"this-is-a-token","name":"this-is-a-token","created_at":null,"last_access":null}]}\n'),
            stdout=self.stdout)
        response = self.stdout.getvalue()
        self.assertEqual(response[-1:], b'\n')
        timstamp, action, error, data = json.loads(response.decode('UTF-8'))
        self.assertEqual(action, 'create')
        self.assertEqual(error, None)
        self.assertEqual(data, {'created_tokens': ['this-is-a-token'], 'id': 'some-generated-uuid', 'name': 'test_user'})

    def _mock_worker_pool(self, cmd, processes, job_iter):
        self.worker_cmd = cmd
        self.worker_processes = processes
        self.worker_jobs = list(job_iter)
        for i, j in self.worker_jobs:
            jname = json.loads(j.decode('UTF-8'))
            yield [[], i, json.dumps(['some-date', None, None, {'id':jname}]
                ).encode('UTF-8') + b'\n']
