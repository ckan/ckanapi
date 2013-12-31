import sys
import ckanapi
import unittest

class TestCallAction(unittest.TestCase):
    def test_local_fail(self):
        self.assertRaises(
            ckanapi.CKANAPIError,
            ckanapi.LocalCKAN('fake').call_action,
            'fake', {}, {}, 'apikey not allowed')

    def test_remote_fail(self):
        self.assertRaises(
            ckanapi.CKANAPIError,
            ckanapi.RemoteCKAN('fake').call_action,
            'fake', {}, 'context not allowed')

    def test_test_fail(self):
        self.assertRaises(
            ckanapi.CKANAPIError,
            ckanapi.TestAppCKAN('fake').call_action,
            'fake', {}, 'context not allowed')

class TestPrepareAction(unittest.TestCase):
    def test_package_list(self):
        observed = ckanapi.prepare_action('package_list')
        expected = ('api/action/package_list', b'{}', {'Content-Type': 'application/json'})
        self.assertEqual(observed, expected)

if __name__ == '__main__':
    unittest.main()
