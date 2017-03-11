import json
import ckanapi.common
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestCommonPrepareAction(unittest.TestCase):
    def test_resource_create_sets_default_url(self):
        _, data_str, _ = ckanapi.common.prepare_action('resource_create')
        data = json.loads(data_str.decode('utf-8'))
        self.assertEqual(data['url'], '')

    def test_resource_create_doesnt_overwrite_received_url(self):
        _, data_str, _ = ckanapi.common.prepare_action('resource_create',
                                                       {'url': 'foo'})
        data = json.loads(data_str.decode('utf-8'))
        self.assertEqual(data['url'], 'foo')
