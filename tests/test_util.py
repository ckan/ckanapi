import ckanapi
import unittest

class TestUtil(unittest.TestCase):
    def test_unpack_request(self):
        class Mock:
            def read(self):
                return 'This is encoded.'.encode('ascii')
            def getcode(self):
                return 200

        mock_request = Mock()
        observed = ckanapi._unpack_request(mock_request)
        expected = (200, 'This is encoded.')
        self.assertEqual(observed, expected)

    def test_prepare_action(self):
        observed = ckanapi.prepare_action('package_list')
        expected = ('api/action/package_list', b'{}', {'Content-Type': 'application/json'})
        self.assertEqual(observed, expected)
