from ckanapi.cli.dump_metadata import dump_metadata
from ckanapi.errors import NotFound
import json
import tempfile
import shutil
from os.path import exists

try:
    import unittest2 as unittest
except ImportError:
    import unittest
from io import BytesIO


class MockCKAN(object):

    def __init__(self):

        self.data = [{'id': '12',
                 'name': 'twelve',
                 'title': "Twelve"},
                {'id': '34',
                 'name': 'thirtyfour',
                 'title': "Thirty-four"},
                {'id': '56',
                 'name': 'fiftysix',
                 'title': "Fifty-Six"},
                {'id': '67',
                 'name': 'sixtyseven',
                 'title': "Sixty-Seven"},
                {'id': 'dp',
                 'name': 'dp',
                 'title': 'Test for datapackage',
                 'resources':[ {'name': 'resource1',
                         'format': 'html',
                         'url':'http://example.com/test-file'}]}]

    def call_action(self, name, kwargs):
        start = kwargs["start"]
        rows = kwargs["rows"]
        return {"count" : 5,
                "results" : self.data[start:start+rows]}


class TestCLIDumpMetadata(unittest.TestCase):
    def setUp(self):
        self.ckan = MockCKAN()
        self.stdout = BytesIO()
        self.stderr = BytesIO()

    def test_dump_metadata(self):
        dump_metadata(self.ckan, {
                '--ckan-user': None,
                '--config': None,
                '--remote': None,
                '--apikey': None,
                '--output': None,
                '--gzip': False,
            }, 2,
            stdout=self.stdout,
            stderr=self.stderr)
        output = self.stdout.getvalue().decode("UTF-8")
        self.assertEqual(output.count("\n"), 5)
        self.assertTrue(r'{"id":"12","name":"twelve","title":"Twelve"}' in output)
        self.assertTrue(r'{"id":"34","name":"thirtyfour","title":"Thirty-four"}' in output)
        self.assertTrue(r'id":"dp"' in output)

