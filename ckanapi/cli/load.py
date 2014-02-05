"""
implementation of load cli command
"""

import sys
import gzip
import json
from datetime import datetime

from ckanapi.errors import (NotFound, NotAuthorized, ValidationError,
    SearchIndexError)
from ckanapi.cli.workers import worker_pool
from ckanapi.cli.utils import completion_stats, compact_json, quiet_int_pipe


def load_things(ckan, thing, arguments):
    """
    create and update datasets, groups and orgs

    The parent process creates a pool of worker processes and hands
    out json lines to each worker as they finish a task. Status of
    last record completed and records being processed is displayed
    on stderr.
    """
    if arguments['--worker']:
        return load_things_worker(ckan, thing, arguments)

    log = None
    if arguments['--log']:
        log = open(arguments['--log'], 'a')

    jsonl_input = sys.stdin
    if arguments['JSONL_INPUT']:
        jsonl_input = open(arguments['JSONL_INPUT'], 'rb')
    if arguments['--gzip']:
        jsonl_input = gzip.GzipFile(fileobj=jsonl_input)

    def line_reader():
        """
        generate stripped records from jsonl
        handles start-record and max-records options
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
            yield num, line.strip()

    cmd = _worker_command_line(thing, arguments)
    processes = int(arguments['--processes'])
    if hasattr(ckan, 'parallel_limit'):
        # add your sites to ckanapi.remoteckan.MY_SITES instead of removing
        processes = min(processes, ckan.parallel_limit)
    stats = completion_stats(processes)
    pool = worker_pool(cmd, processes, line_reader())

    with quiet_int_pipe():
        for job_ids, finished, result in pool:
            timestamp, action, error, response = json.loads(result)

            if not arguments['--quiet']:
                sys.stderr.write('{0} {1} {2} {3} {4} {5}\n'.format(
                    finished,
                    job_ids,
                    next(stats),
                    action,
                    error,
                    compact_json(response) if response else ''))

            if log:
                log.write(compact_json([
                    timestamp,
                    finished,
                    action,
                    error,
                    response,
                    ]) + b'\n')
                log.flush()


def load_things_worker(ckan, thing, arguments):
    """
    a process that accepts lines of json on stdin which is parsed and
    passed to the {thing}_create/update actions.  it produces lines of json
    which are the responses from each action call.
    """
    supported_things = ('datasets', 'groups', 'organizations')
    thing_number = supported_things.index(thing)

    a = ckan.action
    thing_show, thing_create, thing_update = [
        (a.package_show, a.package_create, a.package_update),
        (a.group_show, a.group_create, a.group_update),
        (a.organization_show, a.organization_create, a.organization_update),
        ][thing_number]

    def reply(action, error, response):
        """
        format messages to be sent back to parent process
        """
        sys.stdout.write(compact_json([
            datetime.now().isoformat(),
            action,
            error,
            response]) + b'\n')
        sys.stdout.flush()

    for line in iter(sys.stdin.readline, b''):
        try:
            obj = json.loads(line.decode('utf-8'))
        except UnicodeDecodeError, e:
            obj = None
            reply('read', 'UnicodeDecodeError', unicode(e))
            continue

        if obj:
            existing = None
            if not arguments['--create-only']:
                # use either id or name to locate existing records
                name = obj.get('id')
                if name:
                    try:
                        existing = thing_show(id=name)
                    except NotFound:
                        pass
                    except NotAuthorized as e:
                        reply('show', 'NotAuthorized', unicode(e))
                        continue
                name = obj.get('name')
                if not existing and name:
                    try:
                        existing = thing_show(id=name)
                        # matching id required for *_update
                        obj['id'] = existing['id']
                    except NotFound:
                        pass
                    except NotAuthorized as e:
                        reply('show', 'NotAuthorized', unicode(e))
                        continue

                # FIXME: compare and reply when 'unchanged'?

            if not existing and arguments['--update-only']:
                reply('show', 'NotFound', [obj.get('id'), obj.get('name')])
                continue

            act = 'update' if existing else 'create'
            try:
                if existing:
                    r = thing_update(**obj)
                else:
                    r = thing_create(**obj)
            except ValidationError as e:
                reply(act, 'ValidationError', e.error_dict)
            except SearchIndexError as e:
                reply(act, 'SearchIndexError', unicode(e))
            except NotAuthorized as e:
                reply(act, 'NotAuthorized', unicode(e))
            except NotFound:
                reply(act, 'NotFound', obj)
            else:
                reply(act, None, r['name'])


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
        )

