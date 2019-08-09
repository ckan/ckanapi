from ckanapi.cli.action import action
from ckanapi.errors import CLIError
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from io import BytesIO


class MockCKAN(object):
    def __init__(self, expected_name, expected_args, response,
            expected_files=None):
        self._expected_name = expected_name
        self._expected_args = expected_args
        self._expected_files = expected_files or {}
        self._response = response

    def call_action(self, name, args, context=None, apikey=None, files=None,
                    requests_kwargs=None):
        if name != self._expected_name:
            return ["wrong name", name, self._expected_name]
        if args != self._expected_args:
            return ["wrong args", args, self._expected_args]
        files = dict((f, v.name) for f,v in files.items())
        if files != self._expected_files:
            return ["wrong files", files, self._expected_files]
        return self._response


class TestCLIAction(unittest.TestCase):
    def test_pretty(self):
        ckan = MockCKAN('shake_it', {'who': 'me'}, {"oh": ["right", "on"]})
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=STRING': ['who=me'],
            '--output-json': False,
            '--output-jsonl': False,
            '--input-json': False,
            '--input': None,
            '--insecure': False
            })
        self.assertEqual(b''.join(rval), b"""
{
  "oh": [
    "right",
    "on"
  ]
}
""".lstrip())

    def test_compact(self):
        ckan = MockCKAN('shake_it', {'who': 'me'}, ["right", "on"])
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=STRING': ['who=me'],
            '--output-json': True,
            '--output-jsonl': False,
            '--input-json': False,
            '--input': None,
            '--insecure': False
            })
        self.assertEqual(b''.join(rval), b'["right","on"]\n')

    def test_compact_fallback(self):
        ckan = MockCKAN('shake_it', {'who': 'me'}, {"oh": ["right", "on"]})
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=STRING': ['who=me'],
            '--output-json': False,
            '--output-jsonl': True,
            '--input-json': False,
            '--input': None,
            '--insecure': False
            })
        self.assertEqual(b''.join(rval), b'{"oh":["right","on"]}\n')

    def test_jsonl(self):
        ckan = MockCKAN('shake_it', {'who': 'me'}, [99,98,97])
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=STRING': ['who=me'],
            '--output-json': False,
            '--output-jsonl': True,
            '--input-json': False,
            '--input': None,
            '--insecure': False
            })
        self.assertEqual(b''.join(rval), b'99\n98\n97\n')

    def test_stdin_json(self):
        ckan = MockCKAN('shake_it', {'who': ['just', 'me']}, "yeah")
        rval = action(ckan, {
                'ACTION_NAME': 'shake_it',
                'KEY=STRING': ['who=me'],
                '--output-json': False,
                '--output-jsonl': False,
                '--input-json': True,
                '--input': None,
                '--insecure': False
            },
            stdin=BytesIO(b'{"who":["just","me"]}'),
            )
        self.assertEqual(b''.join(rval), b'"yeah"\n')

    def test_key_json(self):
        ckan = MockCKAN('shake_it', {'who': ['just', 'me']}, "yeah")
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=STRING': ['who:["just", "me"]'],
            '--output-json': False,
            '--output-jsonl': False,
            '--input-json': False,
            '--input': None,
            '--insecure': False
            })
        self.assertEqual(b''.join(rval), b'"yeah"\n')

    def test_bad_arg(self):
        ckan = MockCKAN('shake_it', {'who': 'me'}, "yeah")
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=STRING': ['who'],
            '--output-json': False,
            '--output-jsonl': False,
            '--input-json': False,
            '--input': None,
            '--insecure': False
            })
        self.assertRaises(CLIError, list, rval)

    def test_bad_key_json(self):
        ckan = MockCKAN('shake_it', {'who': 'me'}, "yeah")
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=STRING': ['who:me'],
            '--output-json': False,
            '--output-jsonl': False,
            '--input-json': False,
            '--input': None,
            '--insecure': False
            })
        self.assertRaises(CLIError, list, rval)

    def test_key_string_or_json(self):
        ckan = MockCKAN('shake_it', {'who': 'me=you'}, "yeah")
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=STRING': ['who:"me=you"'],
            '--output-json': False,
            '--output-jsonl': False,
            '--input-json': False,
            '--input': None,
            '--insecure': False
            })
        self.assertEqual(b''.join(rval), b'"yeah"\n')

    def test_key_json_or_string(self):
        ckan = MockCKAN('shake_it', {'who': 'me:you'}, "yeah")
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=STRING': ['who=me:you'],
            '--output-json': False,
            '--output-jsonl': False,
            '--input-json': False,
            '--input': None,
            '--insecure': False
            })
        self.assertEqual(b''.join(rval), b'"yeah"\n')
