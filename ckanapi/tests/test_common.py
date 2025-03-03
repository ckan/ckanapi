import pickle
import unittest

from ckanapi import RemoteCKAN
from ckanapi.common import ActionShortcut


class TestCommon(unittest.TestCase):
    def test_pickling(self):
        with RemoteCKAN('http://localhost:8901') as ckan:
            action_shortcut = ActionShortcut(ckan)
            # Verifies that pickling seems to work. Previously, this could
            # result in errors like:
            # TypeError: ActionShortcut.__getattr__.<locals>.action() takes 0
            #   positional arguments but 1 was given
            pickled = pickle.dumps(action_shortcut)
            unpickled = pickle.loads(pickled)
            # Partially check that the pickling+unpickling worked
            self.assertEqual(action_shortcut._ckan.address,
                             unpickled._ckan.address)
