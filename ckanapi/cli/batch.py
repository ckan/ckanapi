"""
implementation of batch cli command
"""

import sys
import gzip
import json
from datetime import datetime

from ckanapi.errors import (NotFound, NotAuthorized, ValidationError,
    SearchIndexError)
from ckanapi.cli import workers
from ckanapi.cli.utils import completion_stats, compact_json, quiet_int_pipe

try:
    unicode
except NameError:
    unicode = str


def batch_actions(ckan, arguments,
        worker_pool=None, stdin=None, stdout=None, stderr=None):
    """
    call actions from a jsonl file

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
        return batch_actions_worker(ckan, arguments)

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

    cmd = _worker_command_line(arguments)
    processes = int(arguments['--processes'])
    if hasattr(ckan, 'parallel_limit'):
        # add your sites to CKANAPI_MY_SITES instead of removing
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


def batch_actions_worker(ckan, arguments,
        stdin=None, stdout=None):
    """
    a process that accepts lines of json on stdin which is parsed and
    passed to action calls.  it produces lines of json
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

        requests_kwargs = None
        if arguments['--insecure']:
            requests_kwargs = {'verify': False}

        if obj is not None:
            action = obj['action']
            data = obj.get('data', {})
            files = {}
            if arguments['--local-files']:
                try:
                    for fkey, fvalue in obj.get('files', {}).items():
                        f = open(fvalue, 'rb')
                        files[fkey] = f
                except IOError as e:
                    reply('read', 'IOError', {
                        'parameter':fkey,
                        'file_name':fvalue,
                        'error':unicode(e.args[1]),
                        })
                    continue

            try:
                r = ckan.call_action(action, data, files=files,
                                     requests_kwargs=requests_kwargs)
            except ValidationError as e:
                reply(action, 'ValidationError', e.error_dict)
            except SearchIndexError as e:
                reply(action, 'SearchIndexError', unicode(e))
            except NotAuthorized as e:
                reply(action, 'NotAuthorized', unicode(e))
            except NotFound:
                reply(action, 'NotFound', obj)
            else:
                reply(action, None, r)

def _worker_command_line(arguments):
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
        ['ckanapi', 'batch', '--worker']
        + a('--config')
        + a('--ckan-user')
        + a('--remote')
        + a('--apikey')
        + b('--local-files')
        + b('--insecure')
        )
