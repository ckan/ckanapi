import shutil
import os
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
        from ckan.lib.uploader import ResourceUpload
        self._get_action = get_action
        self._ResourceUpload = ResourceUpload

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
        if not data_dict:
            data_dict = []
        if context is None:
            context = self.context
        if apikey:
            # FIXME: allow use of apikey to set a user in context?
            raise CKANAPIError("LocalCKAN.call_action does not support "
                "use of apikey parameter, use context['user'] instead")
        if files:
            return self._handle_files(action, data_dict, context, files)

        # copy dicts because actions may modify the dicts they are passed
        return self._get_action(action)(dict(context), dict(data_dict))

    def _handle_files(self, action, data_dict, context, files):
        if action not in ['resource_create', 'resource_update']:
            raise CKANAPIError("LocalCKAN.call_action only supports file uploads for resources.")

        if action == 'resource_create':
            resource = self._get_action(action)(dict(context), dict(data_dict))
        else:
            resource = dict(data_dict)

        resource_upload = self._ResourceUpload({'id': resource['id']})

        # get first upload, ignore key
        source_file = list(files.values())[0]
        if not resource_upload.storage_path:
            raise CKANAPIError("No storage configured, unable to upload files")

        directory = resource_upload.get_directory(resource['id'])
        filepath = resource_upload.get_path(resource['id'])
        try:
            os.makedirs(directory)
        except OSError as e:
            ## errno 17 is file already exists
            if e.errno != 17:
                raise

        with open(filepath, 'wb+') as dest:
            shutil.copyfileobj(source_file, dest)

        resource['url'] = ('/dataset/%s/resource/%s/download/%s' 
                           % (resource['package_id'], resource['id'], os.path.basename(source_file.name)))
        resource['url_type'] = 'upload'
        self._get_action('resource_update')(dict(context), resource)
        source_file.close()
        return resource
