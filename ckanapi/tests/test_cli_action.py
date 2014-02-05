from ckanapi.cli.action import action
try:
    import unittest2 as unittest
except ImportError:
    import unittest
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

class MockCKAN(object):
    def __init__(self, expected_name, expected_args, response):
        self._expected_name = expected_name
        self._expected_args = expected_args
        self._response = response

    def call_action(self, name, args):
        if name != self._expected_name:
            return ["wrong name", name, self._expected_name]
        if args != self._expected_args:
            return ["wrong args", args, self._expected_args]
        return self._response


class TestCLIAction(unittest.TestCase):
    def test_pretty(self):
        ckan = MockCKAN('shake_it', {'who': 'me'}, {"oh": ["right", "on"]})
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=VALUE': ['who=me'],
            '--plain-json': False,
            '--jsonl': False,
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
            'KEY=VALUE': ['who=me'],
            '--plain-json': True,
            '--jsonl': False,
            })
        self.assertEqual(b''.join(rval), b'["right","on"]\n')

    def test_compact_fallback(self):
        ckan = MockCKAN('shake_it', {'who': 'me'}, {"oh": ["right", "on"]})
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=VALUE': ['who=me'],
            '--plain-json': False,
            '--jsonl': True,
            })
        self.assertEqual(b''.join(rval), b'{"oh":["right","on"]}\n')

    def test_jsonl(self):
        ckan = MockCKAN('shake_it', {'who': 'me'}, [99,98,97])
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=VALUE': ['who=me'],
            '--plain-json': False,
            '--jsonl': True,
            })
        self.assertEqual(b''.join(rval), b'99\n98\n97\n')

