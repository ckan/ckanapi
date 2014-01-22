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
        ckan = MockCKAN('shake_it', {'who': 'baby'}, {"oh": ["right", "on"]})
        rval = action(ckan, {
            'ACTION_NAME': 'shake_it',
            'KEY=VALUE': ['who=baby'],
            '--jsonl': False,
            })
        self.assertEqual(rval,"""
{
  "oh": [
    "right",
    "on"
  ]
}
""".lstrip())



