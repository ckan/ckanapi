from cgi import FieldStorage

from ckanapi.errors import CKANAPIError
from ckanapi.common import ActionShortcut

class LocalCKAN(object):
    """
    An interface to calling actions with get_action() for CKAN plugins.

    :param username: perform action as this user, defaults to the site user
                     and stored as self.username
    :param context: a default context dict to use when calling actions,
                    stored as self.context with username added as its 'user'
                    value
    """
    def __init__(self, username=None, context=None):
        from ckan.logic import get_action
        self._get_action = get_action

        if username is None:
            username = self.get_site_username()
        self.username = username
        self.context = dict(context or [], user=self.username)
        self.action = ActionShortcut(self)

    def get_site_username(self):
        user = self._get_action('get_site_user')({'ignore_auth': True}, ())
        return user['name']

    def call_action(self, action, data_dict=None, context=None, apikey=None,
            files=None):
        """
        :param action: the action name, e.g. 'package_create'
        :param data_dict: the dict to pass to the action, defaults to {}
        :param context: an override for the context to use for this action,
                        remember to include a 'user' when necessary
        :param apikey: not supported
        :param files: None or {field-name: file-to-be-sent, ...}
        """
        # copy dicts because actions may modify the dicts they are passed
        # (CKAN...you so crazy)
        data_dict = dict(data_dict or [])
        context = dict(self.context if context is None else context)
        if apikey:
            # FIXME: allow use of apikey to set a user in context?
            raise CKANAPIError("LocalCKAN.call_action does not support "
                "use of apikey parameter, use context['user'] instead")
        for fieldname in files or []:
            f = files[fieldname]
            filename = f.name
            if isinstance(f, tuple):
                # requests accepts (filename, file, mimetype) tuples
                filename, f = f[:2]
            try:
                f.tell()
            except AttributeError, IOError:
                raise CKANAPIError("LocalCKAN.call_action only supports "
                    "files with random access, not streams. Consider "
                    "writing your file disk or using StringIO.")
            field_storage = FieldStorage()
            field_storage.file = f
            field_storage.filename = filename
            data_dict[fieldname] = field_storage

        return self._get_action(action)(context, data_dict)
