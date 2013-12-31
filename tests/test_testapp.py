
import json
import ckanapi
import unittest
try:
    import paste.fixture
except ImportError:
    from nose.tools import nottest as python2test
else:
    def python2test(func):
        return func

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


# paste has not been ported to Python 3
# https://github.com/Pylons/pyramid/wiki/Python-3-Porting
@python2test
class TestTestAPPCKAN(unittest.TestCase):
    def setUp(self):
        self.test_app = paste.fixture.TestApp(wsgi_app)
        self.ckan = ckanapi.TestAppCKAN(self.test_app)

    def test_simple(self):
        self.assertEquals(
            self.ckan.action.hello_world(), 'how are you?')
    def test_invalid(self):
        self.assertRaises(
            ckanapi.ValidationError,
            self.ckan.action.invalid)
    def test_data(self):
        self.assertEquals(
            self.ckan.action.echo(message='for you'), 'for you')


if __name__ == '__main__':
    unittest.main()
