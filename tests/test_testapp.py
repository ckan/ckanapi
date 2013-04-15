
#from wsgiref.simple_server import make_server
import json
import ckanapi
import unittest
import paste.fixture

def wsgi_app(environ, start_response):

    status = '200 OK'
    headers = [('Content-type', 'text/plain')]

    start_response(status, headers)

    return [json.dumps({'result': 'looks good'})]


class TestTestAPPCKAN(unittest.TestCase):
    def setUp(self):
        self.test_app = paste.fixture.TestApp(wsgi_app)
        self.ckan = ckanapi.TestAppCKAN(self.test_app)

    def test_once(self):
        self.ckan.action.hello_world()


if __name__ == '__main__':
    unittest.main()
