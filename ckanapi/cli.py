"""ckanapi command line interface

Usage:
  ckanapi action ACTION_NAME
          [KEY=VALUE ...] [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
          [-jz]
  ckanapi (load-datasets | load-groups | load-organizations)
          [JSONL_INPUT] [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
          [-s START] [-m MAX] [-p PROCESSES] [-l LOG_FILE] [-n | -o] [-qwz]
  ckanapi (dump-datasets | dump-groups | dump-organizations)
          [JSONL_OUTPUT] [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
          [-p PROCESSES] [-qwz]
  ckanapi (-h | --help)
  ckanapi --version

Options:
  -h --help                 show this screen
  --version                 show version
  -a --apikey=APIKEY        API key to use for remote actions
  -c --config=CONFIG        CKAN configuration file for local actions,
                            defaults to ./development.ini if that file exists
  -j --jsonl                format list response as jsonl instead of default
                            pretty-printed json format
  -l --log=LOG_FILE         append messages generated to LOG_FILE
  -m --max-records=MAX      exit after processing MAX records
  -n --create-only          create new records, don't update existing records
  -o --update-only          update existing records, don't create new records
  -p --processes=PROCESSES  set the number of worker processes [default: 1]
  -q --quiet                don't display progress messages
  -r --remote=URL           URL of CKAN server for remote actions
  -s --start-record=START   start from record number START, where the first
                            record is number 1 [default: 1]
  -u --ckan-user=USER       perform actions as user with this name, uses the
                            site sysadmin user when not specified
  -w --worker               launch worker process, used internally by load-
                            and dump- commands
  -z --gzip                 read/write gzipped data
"""

import sys
import json
from contextlib import contextmanager
from docopt import docopt
from pkg_resources import load_entry_point

from ckanapi.version import __version__
from ckanapi.remoteckan import RemoteCKAN
from ckanapi.localckan import LocalCKAN
from ckanapi.workers import worker_pool
from ckanapi.stats import completion_stats


def parse_arguments():
    # docopt is awesome
    return docopt(__doc__, version=__version__)


def main(running_with_paster=False):
    """
    ckanapi command line entry point
    """
    arguments = parse_arguments()
    if not running_with_paster and not arguments['--remote']:
        return _switch_to_paster(arguments)

    if arguments['--remote']:
        ckan = RemoteCKAN(arguments['--remote'],
            apikey=arguments['--apikey'],
            user_agent="ckanapi-cli/{version} (+{url})".format(
                version=__version__,
                url='https://github.com/open-data/ckanapi'))
    else:
        ckan = LocalCKAN(username=arguments['--ckan-user'])

    if arguments['action']:
        return action(ckan, arguments)

    load_commands = ['load-datasets', 'load-groups', 'load-organizations']
    command = [x for x in load_commands if arguments[x]]
    if command:
        assert len(command) == 1, command
        return load_things(ckan, command[0], arguments)

    dump_commands = ['dump-datasets', 'dump-groups', 'dump-organizations']
    command = [x for x in dump_commands if arguments[x]]
    if command:
        assert len(command) == 1, command
        return dump_things(ckan, command[0], arguments)

    assert 0, arguments # we shouldn't be here


def action(ckan, arguments):
    """
    call an action with KEY=VALUE args, send the result to stdout
    """
    action_args = {}
    for kv in arguments['KEY=VALUE']:
        key, p, value = kv.partition('=')
        action_args[key] = value
    result = ckan.call_action(arguments['ACTION_NAME'], action_args)

    if arguments['--jsonl']:
        if isinstance(result, list):
            for r in result:
                sys.stdout.write(_compact_json(r) + '\n')
        else:
            sys.stdout.write(_compact_json(result) + '\n')
    else:
        sys.stdout.write(_pretty_json(result) + '\n')


def load_things(ckan, command, arguments):
    """
    create and update datasets, groups and orgs

    The parent process creates a pool of worker processes and hands
    out jsonl lines to each worker as they finish a task. Status of
    last record completed and records being processed is displayed
    on stderr.
    """
    if arguments['--worker']:
        return load_things_worker(ckan, command, arguments)

    log = None
    if arguments['--log']:
        log = open(arguments['--log'], 'a')

    jsonl_input = sys.stdin
    if arguments['JSONL_INPUT']
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

    cmd = _worker_command_line(command, arguments)
    processes = int(arguments['--processes'])
    stats = completion_stats(processes)
    pool = worker_pool(cmd, processes, line_reader())

    with _quiet_int_pipe():
        for job_ids, finished, result in pool:
            timestamp, action, error, response = json.loads(result)

            if not arguments['--quiet']:
                sys.stderr.write('{0} {1} {2} {3} {4}\n'.format(
                    finished,
                    job_ids,
                    stats.next(),
                    action,
                    _compact_json(response) if response else ''))

            if log:
                log.write(_compact_json([
                    timestamp,
                    finished,
                    action,
                    error,
                    response,
                    ]) + '\n')
                log.flush()


def _switch_to_paster(arguments):
    """
    With --config we switch to the paster command version of the cli
    """
    sys.argv[1:1] = ["ckanapi"]
    sys.exit(load_entry_point('PasteScript', 'console_scripts', 'paster')())


def _compact_json(r):
    return json.dumps(r, ensure_ascii=False, separators=(',', ':'))


def _pretty_json(r):
    return json.dumps(r, ensure_ascii=False, separators=(',', ': '), indent=2)


def _worker_command_line(command, arguments):
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
    cmd = (
        ['ckanapi', command, '--worker']
        + a('--config')
        + a('--user')
        + a('--remote')
        + a('--apikey')
        + b('--create-only')
        + b('--update-only')
        )

@contextmanager
def _quiet_int_pipe():
    """
    let pipe errors and KeyboardIterrupt exceptions cause silent exit
    """
    try:
        yield
    except KeyboardInterrupt:
        pass
    except IOError, e:
        if e.errno != 32:
            raise
