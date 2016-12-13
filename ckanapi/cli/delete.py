"""
implementation of delete cli command
"""

import sys
import gzip
import json
from datetime import datetime
from itertools import chain
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
        stdout = getattr(sys.__stdout__, 'buffer', sys.__stdout__)
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

    def name_reader():
        """
        handle start-record and max-records options and extract all
        ids or names from each line (e.g. package_search, package_show
        or package_list output)
        record numbers here correspond to names/ids extracted not lines
        """
        start_record = int(arguments['--start-record'])
        max_records = arguments['--max-records']
        if max_records is not None:
            max_records = int(max_records)

        for num, name in enumerate(chain.from_iterable(
                extract_ids_or_names(line) for line in jsonl_input), 1):
            if num < start_record:
                continue
            if max_records is not None and num >= start_record + max_records:
                break
            yield num, compact_json(name)

    cmd = _worker_command_line(thing, arguments)
    processes = int(arguments['--processes'])
    if hasattr(ckan, 'parallel_limit'):
        # add your sites to ckanapi.remoteckan.MY_SITES instead of removing
        processes = min(processes, ckan.parallel_limit)
    stats = completion_stats(processes)
    if not arguments['ID_OR_NAME']:
        pool = worker_pool(cmd, processes, name_reader())
    else:
        pool = worker_pool(cmd, processes, enumerate(
            (compact_json(n) + b'\n' for n in arguments['ID_OR_NAME']), 1))

    with quiet_int_pipe() as errors:
        for job_ids, finished, result in pool:
            if not result:
                # child exited with traceback
                return 1
            timestamp, error, response = json.loads(
                result.decode('utf-8'))

            if not arguments['--quiet']:
                stderr.write(('%s %s %s %s %s\n' % (
                    finished,
                    job_ids,
                    next(stats),
                    error,
                    compact_json(response).decode('utf-8') if response else ''
                    )).encode('utf-8'))

            if log:
                log.write(compact_json([
                    timestamp,
                    finished,
                    error,
                    response,
                    ]) + b'\n')
                log.flush()
    if 'pipe' in errors:
        return 1
    if 'interrupt' in errors:
        return 2


def extract_ids_or_names(line):
    """
    Be generous in what we accept:

    line may contain
    1. a JSON object with an "id" or "name" value (e.g. package_show result)
    2. a JSON object with a "results" value containing a list
       of objects with "id" values (e.g. package_search result)
    3. a JSON string id or name value
    4. a JSON list of string id or name values (e.g. package_list)
    5. a simple string id or name value

    Returns a list of ids or names found in line
    """
    try:
        j = json.loads(line)
    except ValueError:
        return [line.strip()]  # 5
    if isinstance(j, list) and all(
            isinstance(e, unicode) for e in j):
        return j  # 4
    elif isinstance(j, unicode):
        return [j]  # 3
    elif isinstance(j, dict):
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

    # 5 again (e.g. "true" or "null" or something stranger)
    return [line.strip()]


def delete_things_worker(ckan, thing, arguments,
        stdin=None, stdout=None):
    """
    a process that accepts lines of json on stdin which is parsed and
    passed to the {thing}_delete actions.  it produces lines of json
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

    thing_delete = {
        'datasets': 'package_delete',
        'groups': 'group_delete',
        'organizations': 'organization_delete',
        'users': 'user_delete',
        'related': 'related_delete',
        }[thing]

    def reply(error, response):
        """
        format messages to be sent back to parent process
        """
        stdout.write(compact_json([
            datetime.now().isoformat(),
            error,
            response]) + b'\n')
        stdout.flush()

    for line in iter(stdin.readline, b''):
        try:
            name = json.loads(line.decode('utf-8'))
        except UnicodeDecodeError as e:
            reply('UnicodeDecodeError', unicode(e))
            continue

        try:
            ckan.call_action(thing_delete, {'id': name})
        except NotAuthorized as e:
            reply('NotAuthorized', unicode(e))
        except NotFound:
            reply('NotFound', name)
        else:
            reply(None, name)

def _worker_command_line(thing, arguments):
    """
    Create a worker command line suitable for Popen with only the
    options the worker process requires
    """
    def a(name):
        "options with values"
        return [name, arguments[name]] * (arguments[name] is not None)
    return (
        ['ckanapi', 'delete', thing, '--worker']
        + a('--config')
        + a('--ckan-user')
        + a('--remote')
        + a('--apikey')
        )
