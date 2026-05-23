"""
implementation of load cli command
"""

import sys
import gzip
import json
import requests
from datetime import datetime
import re
from urllib.parse import urlparse

from ckanapi.common import REQUEST_TIMEOUT
from ckanapi.errors import (NotFound, NotAuthorized, ValidationError,
    SearchIndexError)
from ckanapi.cli import workers
from ckanapi.cli.utils import completion_stats, compact_json, quiet_int_pipe


def load_things(ckan, thing, arguments,
        worker_pool=None, stdin=None, stdout=None, stderr=None):
    """
    create and update datasets, groups, orgs and users

    The parent process creates a pool of worker processes and hands
    out json lines to each worker as they finish a task. Status of
    last record completed and records being processed is displayed
    on stderr.
    """
    if worker_pool is None:
        worker_pool = workers.worker_pool
    if stdin is None:
        stdin = getattr(sys.stdin, 'buffer', sys.stdin)
    if stdout is None:
        stdout = getattr(sys.__stdout__, 'buffer', sys.__stdout__)
    if stderr is None:
        stderr = getattr(sys.stderr, 'buffer', sys.stderr)

    if arguments['--worker']:
        return load_things_worker(ckan, thing, arguments)

    log = None
    if arguments['--log']:
        log = open(arguments['--log'], 'ab')

    jsonl_input = stdin
    if arguments['--input']:
        jsonl_input = open(arguments['--input'], 'rb')
    if arguments['--gzip']:
        jsonl_input = gzip.GzipFile(fileobj=jsonl_input)

    def line_reader():
        """
        handle start-record and max-records options
        """
        start_record = int(arguments['--start-record'])
        max_records = arguments['--max-records']
        if max_records is not None:
            max_records = int(max_records)
        for num, line in enumerate(jsonl_input, 1): # records start from 1
            if num < start_record:
                continue
            if max_records is not None and num >= start_record + max_records:
                break
            yield num, line

    cmd = _worker_command_line(thing, arguments)
    processes = int(arguments['--processes'])
    if hasattr(ckan, 'parallel_limit'):
        # add your sites to CKANAPI_MY_SITES instead of removing
        processes = min(processes, ckan.parallel_limit)
    stats = completion_stats(processes)
    pool = worker_pool(cmd, processes, line_reader())

    failures = 0
    with quiet_int_pipe() as errors:
        for job_ids, finished, result in pool:
            if not result:
                # child exited with traceback
                return 1
            timestamp, action, error, response = json.loads(
                result.decode('utf-8'))
            if error:
                failures += 1

            if not arguments['--quiet']:
                stderr.write(('%s %s %s %s %s %s\n' % (
                    finished,
                    job_ids,
                    next(stats),
                    action,
                    error,
                    compact_json(response).decode('utf-8') if response else ''
                    )).encode('utf-8'))

            if log:
                log.write(compact_json([
                    timestamp,
                    finished,
                    action,
                    error,
                    response,
                    ]) + b'\n')
                log.flush()
    if 'pipe' in errors:
        return 1
    if 'interrupt' in errors:
        return 2
    if failures:
        return 3


def load_things_worker(ckan, thing, arguments,
        stdin=None, stdout=None):
    """
    a process that accepts lines of json on stdin which is parsed and
    passed to the {thing}_create/update actions.  it produces lines of json
    which are the responses from each action call.
    """
    if stdin is None:
        stdin = getattr(sys.stdin, 'buffer', sys.stdin)
        # hack so that pdb can be used in extension/ckan
        # code called by this worker
        try:
            sys.stdin = open('/dev/tty', 'rb')
        except IOError:
            pass
    if stdout is None:
        stdout = getattr(sys.__stdout__, 'buffer', sys.__stdout__)
        # hack so that "print debugging" can work in extension/ckan
        # code called by this worker
        sys.stdout = sys.stderr

    thing_show, thing_create, thing_update = {
        'datasets': (
            'package_show', 'package_create', 'package_update'),
        'groups': (
            'group_show', 'group_create', 'group_update'),
        'organizations': (
            'organization_show', 'organization_create', 'organization_update'),
        'users': (
            'user_show', 'user_create', 'user_update'),
        'related':(
            'related_show','related_create','related_update'),
        }[thing]

    def reply(action, error, response):
        """
        format messages to be sent back to parent process
        """
        stdout.write(compact_json([
            datetime.now().isoformat(),
            action,
            error,
            response]) + b'\n')
        stdout.flush()

    for line in iter(stdin.readline, b''):
        try:
            obj = json.loads(line.decode('utf-8'))
        except UnicodeDecodeError as e:
            obj = None
            reply('read', 'UnicodeDecodeError', str(e))
            continue

        requests_kwargs = None
        if arguments['--insecure']:
            requests_kwargs = {'verify': False}

        if obj is not None:
            existing = None
            if not arguments['--create-only']:
                # use either id or name to locate existing records
                name = obj.get('id')
                if name:
                    try:
                        existing = ckan.call_action(thing_show,
                            {'id': name,
                             'include_datasets': False,
                             'include_password_hash': True,
                             'include_users': True,
                            },
                            requests_kwargs=requests_kwargs)
                    except NotFound:
                        pass
                    except NotAuthorized as e:
                        reply('show', 'NotAuthorized', str(e))
                        continue
                name = obj.get('name')
                if not existing and name:
                    try:
                        existing = ckan.call_action(thing_show, {'id': name},
                                                    requests_kwargs=requests_kwargs)
                    except NotFound:
                        pass
                    except NotAuthorized as e:
                        reply('show', 'NotAuthorized', str(e))
                        continue

                if existing:
                    _copy_from_existing_for_update(obj, existing, thing)

                # FIXME: compare and reply when 'unchanged'?

            if not existing and arguments['--update-only']:
                reply('show', 'NotFound', [obj.get('id'), obj.get('name')])
                continue

            act = 'update' if existing else 'create'
            try:
                api_token_list = obj.pop('api_token_list', None)  # do not send api_token_list to user actions
                # do not send resource_views & datastore_fields to package actions
                resource_views = {}
                datastore_fields = {}
                if thing == 'datasets' and obj.get('resources'):
                    for r in obj['resources']:
                        # NOTE: will only work with existing Resource IDs in the input,
                        #       documented in the command help.
                        if arguments['--resource-views']:
                            resource_views[r['id']] = r.pop('resource_views', [])
                        if arguments['--datastore-fields']:
                            datastore_fields[r['id']] = r.pop('datastore_fields', [])
                if existing:
                    r = ckan.call_action(thing_update, obj,
                                         requests_kwargs=requests_kwargs)
                else:
                    r = ckan.call_action(thing_create, obj,
                                         requests_kwargs=requests_kwargs)
                if thing == 'datasets' and 'resources' in obj:
                    # NOTE: order is important as Resource uploads may be dependant on DS Fields (XLoader/DataPusher),
                    #       and Resource Views may be dependant on DS and Upload.
                    if arguments['--datastore-fields'] and datastore_fields:  # check if it is needed to update datastore resource fields when creating/updating packages
                        created_tables, skipped_tables = _load_datastore_resource_fields(ckan, datastore_fields, arguments)
                    if arguments['--upload-resources']:  # check if it is needed to upload resources when creating/updating packages
                        _upload_resources(ckan, obj, arguments)
                    if arguments['--resource-views'] and resource_views:  # check if it is needed to create resource views when creating/updating packages
                        created_views, updated_views, skipped_views = _load_resource_views(ckan, resource_views, arguments)
                if thing in ['groups','organizations'] and 'image_display_url' in obj:  # load images for groups and organizations
                    if arguments['--upload-logo']:
                        users = obj['users']
                        obj = _upload_logo(ckan,obj)
                        obj.pop('image_upload')
                        obj['users'] = users
                        ckan.call_action(thing_update, obj,
                                         requests_kwargs=requests_kwargs)
                if thing == 'users' and arguments['--api-tokens'] and api_token_list:  # check if it is needed to create user api tokens when creating/updating users
                    created_tokens = _load_user_api_tokens(ckan, api_token_list, arguments)
            except ValidationError as e:
                reply(act, 'ValidationError', e.error_dict)
            except SearchIndexError as e:
                reply(act, 'SearchIndexError', str(e))
            except NotAuthorized as e:
                reply(act, 'NotAuthorized', str(e))
            except NotFound:
                reply(act, 'NotFound', obj)
            else:
                log_obj = {'id': r.get('id'), 'name': r.get('name')}
                if thing == 'users' and arguments['--api-tokens'] and api_token_list and created_tokens:
                    log_obj['created_tokens'] = created_tokens
                if thing == 'datasets' and arguments['--resource-views'] and resource_views:
                    if created_views:
                        log_obj['created_resource_views'] = created_views
                    if updated_views:
                        log_obj['updated_resource_views'] = updated_views
                    if skipped_views:
                        log_obj['skipped_resource_views'] = skipped_views
                if thing == 'datasets' and arguments['--datastore-fields'] and datastore_fields:
                    if created_tables:
                        log_obj['created_datastore_tables'] = created_tables
                    if skipped_tables:
                        log_obj['skipped_datastore_tables'] = skipped_tables
                reply(act, None, log_obj)

def _worker_command_line(thing, arguments):
    """
    Create a worker command line suitable for Popen with only the
    options the worker process requires
    """
    def a(name):
        "options with values"
        return [name, arguments[name]] * (arguments[name] is not None)
    def b(name):
        "boolean options"
        return [name] * bool(arguments[name])
    return (
        ['ckanapi', 'load', thing, '--worker']
        + a('--config')
        + a('--ckan-user')
        + a('--remote')
        + a('--apikey')
        + b('--create-only')
        + b('--update-only')
        + b('--upload-resources')
        + b('--upload-logo')
        + b('--api-tokens')
        + b('--datastore-fields')
        + b('--resource-views')
        )


def _copy_from_existing_for_update(obj, existing, thing):
    """
    modifies obj dict in place, copying values from existing.

    the id is alwasys copied from existing to make sure update updates
    the correct object.

    users lists for groups and orgs are maintained if not present in obj
    """
    if 'id' in existing:
        obj['id'] = existing['id']

    if thing in ('organizations', 'groups'):
        if 'users' not in obj and 'users' in existing:
            obj['users'] = existing['users']


def _upload_resources(ckan, obj, arguments):
    resources = obj['resources']
    requests_kwargs = None
    if arguments['--insecure']:
        requests_kwargs = {'verify': False}
    for resource in resources:
        if resource.get('url_type') != 'upload':
            continue

        f = requests.get(resource['url'], stream=True, timeout=REQUEST_TIMEOUT)
        name = resource['url'].rsplit('/',1)[-1]
        ckan.call_action('resource_patch',
            {'id':resource['id']},
            files={'upload':(name, f.raw)},
            requests_kwargs=requests_kwargs)


def _load_resource_views(ckan, resource_views, arguments):
    """
    Loads resource views
    """
    created = []
    updated = []
    skipped = []
    requests_kwargs = None
    if arguments['--insecure']:
        requests_kwargs = {'verify': False}
    for rid, views in resource_views.items():
        for view in views:
            existing = None
            view['resource_id'] = rid
            if not arguments['--create-only']:
                if view.get('id'):
                    try:
                        existing = ckan.call_action('resource_view_show',
                            {'id': view['id']},
                            requests_kwargs=requests_kwargs)
                    except NotFound:
                        pass

                if existing:
                    _copy_from_existing_for_update(view, existing, 'resource_view')

            if not existing and arguments['--update-only']:
                skipped.append(view.get('id', view.get('view_type')))
                continue

            if existing:
                # exceptions handled in load_things_worker
                ckan.call_action('resource_view_update', view,
                                requests_kwargs=requests_kwargs)
                updated.append(view.get('id', view.get('view_type')))
            else:
                # exceptions handled in load_things_worker
                ckan.call_action('resource_view_create', view,
                                requests_kwargs=requests_kwargs)
                created.append(view.get('id', view.get('view_type')))

    return created, updated, skipped


def _load_datastore_resource_fields(ckan, datastore_fields, arguments):
    """
    Load datastore tables for Resources
    """
    created = []
    skipped = []
    requests_kwargs = None
    if arguments['--insecure']:
        requests_kwargs = {'verify': False}
    for rid, ds_fields in datastore_fields.items():
        if not ds_fields:
            continue
        existing = None
        try:
            existing = ckan.call_action('datastore_search',
                {'resource_id': rid, 'limit': 0},
                requests_kwargs=requests_kwargs)
        except NotFound:
            pass

        try:
            ckan.call_action(
                'datastore_create',
                {
                    'resource_id': rid,
                    'fields': ds_fields,
                    'force': True
                },
                requests_kwargs=requests_kwargs)
            created.append(rid)
        except ValidationError as e:
            if not existing:
                # exceptions handled in load_things_worker
                # raise normal exception for non-existing tables
                raise e
            skipped.append('%s: %s' % (rid, e))

    return created, skipped


def _upload_logo(ckan,obj_orig):
    obj = obj_orig.copy()
    for key in obj_orig.keys():
        if isinstance(obj[key],(dict,list)):
            obj.pop(key)                            #dict/list objects can't be encoded
    if urlparse(obj['image_url']).netloc:                  # logo is an external link
        obj['clear_upload'] = True
        obj['image_upload'] = obj['image_url']
    else:
        f = requests.get(obj['image_display_url'], stream=True, timeout=REQUEST_TIMEOUT)
        name,ext = obj['image_url'].rsplit('.',1)  #reformulate image_url for new site
        new_name = re.sub('[0-9.-]','',name)
        new_url = new_name+'.'+ext
        obj['image_upload'] = (new_url, f.raw)
    ckan.action.group_update(**obj)
    return obj


def _load_user_api_tokens(ckan, api_token_list, arguments):
    """
    Loads user API Tokens from api_token_list
    """
    requests_kwargs = None
    if arguments['--insecure']:
        requests_kwargs = {'verify': False}
    created_tokens = []
    for token in api_token_list:
        # exceptions handled in load_things_worker
        ckan.call_action(
            'api_token_create',
            {
                'id': token['id'],
                'created_at': token['created_at'],
                'last_access': token['last_access'],
                'name': token['name'],
                'user': token['user_id']
            },
            requests_kwargs=requests_kwargs)
        created_tokens.append(token['name'])
    return created_tokens
