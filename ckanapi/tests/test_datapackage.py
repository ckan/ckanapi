from ckanapi.datapackage import (
    dataset_to_datapackage, create_resource, create_datapackage,
    resource_filename, populate_schema_from_datastore)

try:
    import unittest2 as unittest
except ImportError:
    import unittest
from io import BytesIO
import os
from pyfakefs import fake_filesystem_unittest


class TestDatasetToDataPackage(unittest.TestCase):
    def test_simple_dataset(self):
        dataset_dict = {
            u'extras': [{u'key': u'subject', u'value': u'science'}],
            u'name': u'test_dataset_00',
            u'notes': u'Just another test dataset.',
            u'resources': [{
                u'format': u'PNG',
                u'name': u'Image 1',
                u'url': u'http://example.com/image.png',
                }],
            u'tags': [{
                u'display_name': u'science',
                u'id': u'59f9359c-002b-4166-a519-755f89a631da',
                u'name': u'science',
            }],
            u'title': u'Test Dataset',
            u'type': u'dataset',
        }

        datapackage = dataset_to_datapackage(dataset_dict)

        # code copied from test_package_show_with_full_dataset()
        assert datapackage == {
            u'description': u'Just another test dataset.',
            u'extras': {u'subject': u'science'},
            u'keywords': [u'science'],
            u'name': u'test_dataset_00',
            u'resources': [{u'format': u'PNG',
                            u'name': u'image-1',
                            u'path': u'http://example.com/image.png',
                            u'title': u'Image 1'}],
            u'title': u'Test Dataset'}

    def test_full_dataset(self):
        # This sample dataset_dict was generated in CKAN along the lines of
        # ckan/tests/logic/action/test_get.py
        # TestPackageShow.test_package_show_with_full_dataset()
        dataset_dict = {
            u'author': None,
            u'author_email': None,
            u'creator_user_id': u'3267d399-5517-47ef-ac02-13bb29372428',
            u'extras': [{u'key': u'subject', u'value': u'science'}],
            u'groups': [{u'description': u'A test description for this test group.',
                        u'display_name': u'Test Group 00',
                        u'id': u'cca3543f-0ba0-4194-b2f3-326498eb88b7',
                        u'image_display_url': u'',
                        u'name': u'test_group_00',
                        u'title': u'Test Group 00'}],
            u'id': u'a7165429-dde3-4a5f-ba7d-c690209200cf',
            u'isopen': False,
            u'license_id': None,
            u'license_title': None,
            u'maintainer': None,
            u'maintainer_email': None,
            u'metadata_created': u'2019-05-24T16:30:43.889152',
            u'metadata_modified': u'2019-05-24T16:30:43.889161',
            u'name': u'test_dataset_00',
            u'notes': u'Just another test dataset.',
            u'num_resources': 1,
            u'num_tags': 1,
            u'organization': {
                u'approval_status': u'approved',
                u'created': u'2019-05-24T16:30:43.608032',
                u'description': u'Just another test organization.',
                u'id': u'aa878f8c-1f6e-4e87-b08e-67272d9c3d16',
                u'image_url': u'http://placekitten.com/g/200/100',
                u'is_organization': True,
                u'name': u'test_org_00',
                u'revision_id': u'bb31cfee-aee9-4031-9333-ed922bf3f049',
                u'state': u'active',
                u'title': u'Test Organization',
                u'type': u'organization'},
            u'owner_org': u'aa878f8c-1f6e-4e87-b08e-67272d9c3d16',
            u'private': False,
            u'relationships_as_object': [],
            u'relationships_as_subject': [],
            u'resources': [{
                u'cache_last_updated': None,
                u'cache_url': None,
                u'created': u'2019-05-24T16:30:43.894623',
                u'description': u'',
                u'format': u'PNG',
                u'hash': u'',
                u'id': u'a8e2f627-0450-4728-a0a4-ed3a091c303c',
                u'last_modified': None,
                u'mimetype': None,
                u'mimetype_inner': None,
                u'name': u'Image 1',
                u'package_id': u'a7165429-dde3-4a5f-ba7d-c690209200cf',
                u'position': 0,
                u'resource_type': None,
                u'revision_id': u'990df889-690c-412e-a7ad-f848c9927218',
                u'size': None,
                u'state': u'active',
                u'url': u'http://example.com/image.png',
                u'url_type': None}],
            u'revision_id': u'990df889-690c-412e-a7ad-f848c9927218',
            u'state': u'active',
            u'tags': [{
                u'display_name': u'science',
                u'id': u'59f9359c-002b-4166-a519-755f89a631da',
                u'name': u'science',
                u'state': u'active',
                u'vocabulary_id': None}],
            u'title': u'Test Dataset',
            u'type': u'dataset',
            u'url': None,
            u'version': None
        }

        datapackage = dataset_to_datapackage(dataset_dict)

        assert datapackage == {
            u'description': u'Just another test dataset.',
            u'extras': {u'subject': u'science'},
            u'keywords': [u'science'],
            u'name': u'test_dataset_00',
            u'resources': [{u'format': u'PNG',
                            u'name': u'image-1',
                            u'path': u'http://example.com/image.png',
                            u'title': u'Image 1'}],
            u'title': u'Test Dataset'}

    def test_resource_names_are_unique(self):
        # Somehow these resources got the same name
        dataset_dict = {
            u'name': u'test_dataset_00',
            u'notes': u'Just another test dataset.',
            u'resources': [
                {
                    u'format': u'PNG',
                    u'name': u'Image',
                    u'url': u'http://example.com/imageA.png',
                },
                {
                    u'format': u'PNG',
                    u'name': u'Image',
                    u'url': u'http://example.com/imageB.png',
                },
                {
                    u'format': u'PNG',
                    u'name': u'Image',
                    u'url': u'http://example.com/imageC.png',
                },
                ],
            u'tags': [{
                u'display_name': u'science',
                u'id': u'59f9359c-002b-4166-a519-755f89a631da',
                u'name': u'science',
            }],
            u'title': u'Test Dataset',
            u'type': u'dataset',
        }

        datapackage = dataset_to_datapackage(dataset_dict)

        assert [res['name'] for res in datapackage['resources']] == \
            [u'image', u'image0', u'image1']


class TestCreateResource(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_simple(self):
        resource = {
            u'format': u'PNG',
            u'name': u'Image',
            u'url': u'http://example.com/image.png',
        }
        filename = 'image_saved.png'
        os.makedirs('/test/data')
        stderr = BytesIO()
        # TODO mock the HTTP request to example.com

        returned_resource = create_resource(
            resource, filename='image_saved.png',
            datapackage_dir='/test', stderr=stderr)

        stderr.seek(0)
        assert not stderr.read()
        assert returned_resource == {
            u'url': u'http://example.com/image.png',
            u'name': u'Image',
            u'format': u'PNG',
            u'path': u'data/image_saved.png',
        }


class TestCreateDataPackage(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_simple(self):
        dataset = {
            u'extras': [{u'key': u'subject', u'value': u'science'}],
            u'name': u'test_dataset_00',
            u'notes': u'Just another test dataset.',
            u'resources': [{
                u'format': u'PNG',
                u'name': u'Image 1',
                u'url': u'http://example.com/image.png',
                }],
            u'tags': [{
                u'display_name': u'science',
                u'id': u'59f9359c-002b-4166-a519-755f89a631da',
                u'name': u'science',
            }],
            u'title': u'Test Dataset',
            u'type': u'dataset',
        }
        stderr = BytesIO()
        os.makedirs('/test/data')
        # TODO mock the HTTP request to example.com

        datapackage_dir, datapackage, json_path = \
            create_datapackage(record=dataset, base_path='/test/',
                               stderr=stderr)

        stderr.seek(0)
        assert not stderr.read()
        assert datapackage_dir == u'/test/test_dataset_00'
        assert datapackage == {
            u'name': u'test_dataset_00',
            u'description': u'Just another test dataset.',
            u'title': u'Test Dataset',
            u'extras': {u'subject': u'science'},
            u'keywords': [u'science'],
            u'resources': [{
                u'path': u'data/image-1.png',  # i.e. it was downloaded
                u'title': u'Image 1',
                u'name': u'image-1',
                u'format': u'PNG'}],
        }
        assert json_path == u'/test/test_dataset_00/datapackage.json'


class TestResourceFilename(unittest.TestCase):
    def test_simple(self):
        datapackage_resource = {
            u'title': u'Image 1',
            u'name': u'image-1',
            u'format': u'PNG'
        }

        filename = resource_filename(dres=datapackage_resource)

        assert filename == u'image-1.png'


class TestPopulateSchemaFromDatastore(unittest.TestCase):
    def test_simple(self):
        ckan_resource = {
            u'format': u'CSV',
            u'name': u'Buildings 1',
            u'url': u'http://example.com/buildings.csv',
            # example datastore fields from:
            # curl 'https://data.boston.gov/api/3/action/datastore_search?resource_id=28ca9f8d-f6ad-4855-bf14-90d2d0bc85ca&limit=0' |jq '.result.fields'
            u'datastore_fields': [
                {
                    u'id': u'country',
                    u'type': u'int',
                    u'info': {
                        u'label': u'The country',
                        u'notes': u'iso code',
                    }
                },
                {
                    u'id': u'NUM_FLOORS',
                    u'type': u'text',
                    u'info': {
                        u'type_override': {}
                    },
                }
            ]
        }
        datapackage_resource = {
            u'title': u'Buildings 1',
            u'name': u'buildings-1',
            u'format': u'CSV'
        }

        populate_schema_from_datastore(cres=ckan_resource,
                                       dres=datapackage_resource)

        assert datapackage_resource == {
            u'title': u'Buildings 1',
            u'name': u'buildings-1',
            u'format': u'CSV',
            u'schema': {'fields': [{'description': u'iso code',
                                    'name': u'country',
                                    'title': u'The country'},
                                   {'name': u'NUM_FLOORS',
                                    'type': 'string'}]
            }
        }
