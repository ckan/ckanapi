
import json

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import ckanapi

def wsgi_app(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'application/json')]

    path = environ['PATH_INFO']
    if path == '/api/action/hello_world':
        response = {'success': True, 'result': 'how are you?'}
    elif path == '/api/action/invalid':
        response = {'success': False, 'error': {'__type': 'Validation Error'}}
    elif path == '/api/action/echo':
        response = {'success': True, 'result':
            json.loads(environ['wsgi.input'].read())['message']}

    start_response(status, headers)
    return [json.dumps(response)]


class TestTestAPPCKAN(unittest.TestCase):
    def setUp(self):
        try:
            import paste.fixture
        except ImportError:
            raise unittest.SkipTest('paste not importable')
        self.test_app = paste.fixture.TestApp(wsgi_app)
        self.ckan = ckanapi.TestAppCKAN(self.test_app)

    def test_simple(self):
        self.assertEqual(
            self.ckan.action.hello_world(), 'how are you?')
    def test_invalid(self):
        self.assertRaises(
            ckanapi.ValidationError,
            self.ckan.action.invalid)
    def test_data(self):
        self.assertEqual(
            self.ckan.action.echo(message='for you'), 'for you')
