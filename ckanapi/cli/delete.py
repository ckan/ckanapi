"""
implementation of load cli command
"""

import sys
import gzip
import json
from datetime import datetime
import re
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from ckanapi.errors import (NotFound, NotAuthorized, ValidationError,
    SearchIndexError)
from ckanapi.cli import workers
from ckanapi.cli.utils import completion_stats, compact_json, quiet_int_pipe

try:
    unicode
except NameError:
    unicode = str

def delete_things(ckan, thing, arguments,
        worker_pool=None, stdin=None, stdout=None, stderr=None):
    """
    delete datasets, groups, orgs, users etc,

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
        stdout = getattr(sys.stdout, 'buffer', sys.stdout)
    if stderr is None:
        stderr = getattr(sys.stderr, 'buffer', sys.stderr)

    if arguments['--worker']:
        return delete_things_worker(ckan, thing, arguments)

    log = None
    if arguments['--log']:
        log = open(arguments['--log'], 'a')

    jsonl_input = stdin
    if arguments['--input']:
        jsonl_input = open(arguments['--input'], 'rb')
    if arguments['--gzip']:
        jsonl_input = gzip.GzipFile(fileobj=jsonl_input)

    def line_reader():
        """
        handle start-record and max-records options and extract all
        ids or names from each line (e.g. package_search output)
        numbers correspond to names/ids extracted not lines
        """
        start_record = int(arguments['--start-record'])
        max_records = arguments['--max-records']
        if max_records is not None:
            max_records = int(max_records)
        num = 1  # records start from 1
        for line in jsonl_input:

            if num < start_record:
                continue
            if max_records is not None and num >= start_record + max_records:
                break
            yield num, line

    cmd = _worker_command_line(thing, arguments)
    processes = int(arguments['--processes'])
    if hasattr(ckan, 'parallel_limit'):
        # add your sites to ckanapi.remoteckan.MY_SITES instead of removing
        processes = min(processes, ckan.parallel_limit)
    stats = completion_stats(processes)
    pool = worker_pool(cmd, processes, line_reader())

    with quiet_int_pipe() as errors:
        for job_ids, finished, result in pool:
            if not result:
                # child exited with traceback
                return 1
            timestamp, action, error, response = json.loads(
                result.decode('utf-8'))

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


def extract_id_or_name(line):
    """
    Be generous in what we accept:

    line may contain
    1. a JSON object with an "id" or "name" value
    2. a JSON object with a "results" value containing a list
       of objects with "id" values (i.e. result from package_search)
    3. a JSON string id or name value
    4. a simple string id or name value

    Returns a list of ids or names found in line
    """
    try:
        j = json.loads(line)
    except ValueError:
        return [line.strip()]  # 4
    if isinstance(j, unicode):
        return [j]  # 3
    if isinstance(j, dict):
        if 'id' in j and isinstance(j['id'], unicode):
            return [j['id']]  # 1
        if 'name' in j and isinstance(j['name'], unicode):
            return [j['name']]  # 1 again
        if 'results' in j and isinstance(j['results'], list):
            out = []
            for r in j['results']:
                if (not isinstance(r, dict) or 'id' not in r or
                        not isinstance(r['id'], unicode)):
                    break
                out.append(r['id'])
            else:
                return out

    # 4 again (e.g. "true" or "null" or something stranger)
    return [line.strip()]



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
        stdout = getattr(sys.stdout, 'buffer', sys.stdout)
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
            reply('read', 'UnicodeDecodeError', unicode(e))
            continue

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
                            })
                    except NotFound:
                        pass
                    except NotAuthorized as e:
                        reply('show', 'NotAuthorized', unicode(e))
                        continue
                name = obj.get('name')
                if not existing and name:
                    try:
                        existing = ckan.call_action(thing_show, {'id': name})
                    except NotFound:
                        pass
                    except NotAuthorized as e:
                        reply('show', 'NotAuthorized', unicode(e))
                        continue

                if existing:
                    _copy_from_existing_for_update(obj, existing, thing)

                # FIXME: compare and reply when 'unchanged'?

            if not existing and arguments['--update-only']:
                reply('show', 'NotFound', [obj.get('id'), obj.get('name')])
                continue

            act = 'update' if existing else 'create'
            try:
                if existing:
                    r = ckan.call_action(thing_update, obj)
                else:
                    r = ckan.call_action(thing_create, obj)
                if thing == 'datasets' and 'resources' in obj:# check if it is needed to upload resources when creating/updating packages
                    _upload_resources(ckan,obj,arguments)
                elif thing in ['groups','organizations'] and 'image_display_url' in obj:   #load images for groups and organizations
                    if arguments['--upload-logo']:
                        users = obj['users']
                        _upload_logo(ckan,obj)
                        obj.pop('image_upload')
                        obj['users'] = users
                        ckan.call_action(thing_update,obj)
            except ValidationError as e:
                reply(act, 'ValidationError', e.error_dict)
            except SearchIndexError as e:
                reply(act, 'SearchIndexError', unicode(e))
            except NotAuthorized as e:
                reply(act, 'NotAuthorized', unicode(e))
            except NotFound:
                reply(act, 'NotFound', obj)
            else:
                reply(act, None, r.get('name',r.get('id')))

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

def _upload_resources(ckan,obj,arguments):
    resources = obj['resources']
    if len(resources)==0:
        return
    for resource in resources:
        if resource.get('url_type') == 'upload':      # check for same domain resources
            for key in resource.keys():
                if isinstance(resource[key],(dict,list)):
                    resource.pop(key)                # dict/list objects can't be encoded
            if arguments['--upload-resources']:
                f = requests.get(resource['url'],stream=True)
                new_url = resource['url'].rsplit('/',1)[-1]
                resource['upload'] = (new_url,f.raw)
            else:
                resource['url_type'] = ''           # hack url_type so that url can be modified
                resource['package_id'] = obj['name']
            ckan.action.resource_update(**resource)


def _upload_logo(ckan,obj):
    for key in obj.keys():
        if isinstance(obj[key],(dict,list)):
            obj.pop(key)                            #dict/list objects can't be encoded
    if urlparse(obj['image_url']).netloc:                  # logo is an external link
        obj['clear_upload'] = True
        obj['image_upload'] = obj['image_url']
    else:
        f = requests.get(obj['image_display_url'],stream=True)
        name,ext = obj['image_url'].rsplit('.',1)  #reformulate image_url for new site
        new_name = re.sub('[0-9\.-]','',name)
        new_url = new_name+'.'+ext
        obj['image_upload'] = (new_url, f.raw)
    ckan.action.group_update(**obj)
