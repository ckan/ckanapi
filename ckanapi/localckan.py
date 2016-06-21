from cgi import FieldStorage
from tempfile import TemporaryFile

from ckanapi.errors import CKANAPIError
from ckanapi.common import ActionShortcut

COPY_CHUNK = 1024*1024

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

        to_close = []
        try:
            for fieldname in files or []:
                f = files[fieldname]
                if isinstance(f, tuple):
                    # requests accepts (filename, file...) tuples
                    filename, f = f[:2]
                else:
                    filename = f.name
                try:
                    f.seek(0)
                except (AttributeError, IOError):
                    f = _write_temp_file(f)
                    to_close.append(f)
                field_storage = FieldStorage()
                field_storage.file = f
                field_storage.filename = filename
                data_dict[fieldname] = field_storage

            return self._get_action(action)(context, data_dict)
        finally:
            for f in to_close:
                f.close()


def _write_temp_file(f):
    """
    Pull all data from stream f into a temporary file

    Caller must close file returned.
    """
    out = TemporaryFile()
    while True:  # FIXME: check for maximum size?
        chunk = f.read(COPY_CHUNK)
        if not chunk:
            break
        out.write(chunk)
    return out
