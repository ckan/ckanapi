"""ckanapi command line interface

Usage:
  ckanapi action ACTION_NAME
          [KEY=VALUE ...] [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
          [-jz]
  ckanapi (load-datasets | load-groups | load-organizations)
          [JSONL_INPUT] [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
          [-s START] [-m MAX] [-p PROCESSES] [-l LOG_FILE] [-n | -o] [-qz]
  ckanapi (dump-datasets | dump-groups | dump-organizations)
          [JSONL_OUTPUT] [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
          [-p PROCESSES] [-qz]
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
  -s --start-record=START   start from record number START [default: 1]
  -u --ckan-user=USER       perform actions as user with this name, uses the
                            site sysadmin user when not specified
  -z --gzip                 read/write gzipped data
"""

import sys
import json
from docopt import docopt
from pkg_resources import load_entry_point

from ckanapi.version import __version__
from ckanapi.remoteckan import RemoteCKAN
from ckanapi.localckan import LocalCKAN

def main(running_with_paster=False):
    """
    ckanapi command line entry point

    :param ckan: a LocalCKAN instance when launched from paster
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
    call an action with KEY=VALUE args, output the result on success
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


def parse_arguments():
    return docopt(__doc__, version=__version__)


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
