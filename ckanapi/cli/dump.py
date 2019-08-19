"""
implementation of dump cli command
"""

import sys
import gzip
import json
from datetime import datetime
import os

from ckanapi.errors import (NotFound, NotAuthorized, ValidationError,
    SearchIndexError)
from ckanapi.cli import workers
from ckanapi.cli.utils import completion_stats, compact_json, \
    quiet_int_pipe
from ckanapi.datapackage import create_datapackage, \
    populate_datastore_res_fields


def dump_things(ckan, thing, arguments,
        worker_pool=None, stdout=None, stderr=None):
    """
    dump all datasets, groups, orgs or users accessible by the connected user

    The parent process creates a pool of worker processes and hands
    out ids to each worker. Status of last record completed and records
    being processed is displayed on stderr.
    """
    if worker_pool is None:
        worker_pool = workers.worker_pool
    if stdout is None:
        stdout = getattr(sys.__stdout__, 'buffer', sys.__stdout__)
    if stderr is None:
        stderr = getattr(sys.stderr, 'buffer', sys.stderr)

    if arguments['--worker']:
        return dump_things_worker(ckan, thing, arguments)

    log = None
    if arguments['--log']:
        log = open(arguments['--log'], 'a')

    jsonl_output = stdout
    if arguments['--datapackages']:  # TODO: do we want to just divert this to devnull?
        jsonl_output = open(os.devnull, 'wb')
    if arguments['--output']:
        jsonl_output = open(arguments['--output'], 'wb')
    if arguments['--gzip']:
        jsonl_output = gzip.GzipFile(fileobj=jsonl_output)
    if arguments['--all']:
        get_thing_list = {
            'datasets': 'package_list',
            'groups': 'group_list',
            'organizations': 'organization_list',
            'users': 'user_list',
            'related' :'related_list',
            }[thing]
        params = dict(
            all_fields=False,  # for user_list
            )
        names = ckan.call_action(get_thing_list, params)

    else:
        names = arguments['ID_OR_NAME']

    if names and isinstance(names[0], dict):
        names = [rec.get('name',rec.get('id')) for rec in names]

    if arguments['--datapackages']:
        arguments['--datastore-fields'] = True
    cmd = _worker_command_line(thing, arguments)
    processes = int(arguments['--processes'])
    if hasattr(ckan, 'parallel_limit'):
        # add your sites to ckanapi.remoteckan.MY_SITES instead of removing
        processes = min(processes, ckan.parallel_limit)
    stats = completion_stats(processes)
    pool = worker_pool(cmd, processes,
        enumerate(compact_json(n) + b'\n' for n in names))

    results = {}
    expecting_number = 0
    with quiet_int_pipe() as errors:
        for job_ids, finished, result in pool:
            if not result:
                # child exited with traceback
                return 1
            timestamp, error, record = json.loads(result.decode('utf-8'))
            results[finished] = record

            if not arguments['--quiet']:
                stderr.write('{0} {1} {2} {3} {4}\n'.format(
                    finished,
                    job_ids,
                    next(stats),
                    error,
                    record.get('name', '') if record else '',
                    ).encode('utf-8'))

            if log:
                log.write(compact_json([
                    timestamp,
                    finished,
                    error,
                    record.get('name', '') if record else None,
                    ]) + b'\n')

            datapackages_path = arguments['--datapackages']
            if datapackages_path:
                create_datapackage(record, datapackages_path, stderr)

            # keep the output in the same order as names
            while expecting_number in results:
                record = results.pop(expecting_number)
                if record:
                    # sort keys so we can diff output
                    jsonl_output.write(compact_json(record,
                        sort_keys=True) + b'\n')
                expecting_number += 1
    if 'pipe' in errors:
        return 1
    if 'interrupt' in errors:
        return 2


def dump_things_worker(ckan, thing, arguments,
        stdin=None, stdout=None):
    """
    a process that accepts names on stdin which are
    passed to the {thing}_show actions.  it produces lines of json
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

    thing_show = {
        'datasets': 'package_show',
        'groups': 'group_show',
        'organizations': 'organization_show',
        'users': 'user_show',
        'related':'related_show'
        }[thing]

    def reply(error, record=None):
        """
        format messages to be sent back to parent process
        """
        stdout.write(compact_json([
            datetime.now().isoformat(),
            error,
            record]) + b'\n')
        stdout.flush()

    for line in iter(stdin.readline, b''):
        try:
            name = json.loads(line.decode('utf-8'))
        except UnicodeDecodeError as e:
            reply('UnicodeDecodeError')
            continue

        try:
            requests_kwargs = None
            if arguments['--insecure']:
                requests_kwargs = {'verify': False}
            obj = ckan.call_action(thing_show, {'id': name,
                'include_datasets': False,
                'include_password_hash': True,
                }, requests_kwargs=requests_kwargs)
        except NotFound:
            reply('NotFound')
        except NotAuthorized:
            reply('NotAuthorized')
        else:
            if thing == 'datasets' and arguments['--datastore-fields']:
                for res in obj.get('resources', []):
                    populate_datastore_res_fields(ckan, res)
            reply(None, obj)

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
        ['ckanapi', 'dump', thing, '--worker']
        + a('--config')
        + a('--ckan-user')
        + a('--remote')
        + a('--apikey')
        + b('--get-request')
        + b('--datastore-fields')
        + ['value-here-to-make-docopt-happy']
        )
