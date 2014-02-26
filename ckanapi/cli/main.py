"""ckanapi command line interface

Usage:
  ckanapi action ACTION_NAME
          [KEY=VALUE ... | -i] [-j | -J]
          [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY] [-g]]
  ckanapi load (datasets | groups | organizations)
          [-I JSONL_INPUT] [-s START] [-m MAX] [-p PROCESSES] [-l LOG_FILE]
          [-n | -o] [-qwz] [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
  ckanapi dump (datasets | groups | organizations)
          (ID_OR_NAME ... | --all) [-O JSONL_OUTPUT] [-p PROCESSES] [-qwz]
          [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
  ckanapi (-h | --help)
  ckanapi --version

Options:
  -h --help                 show this screen
  --version                 show version
  -a --apikey=APIKEY        API key to use for remote actions
  --all                     all the things
  -c --config=CONFIG        CKAN configuration file for local actions,
                            defaults to ./development.ini if that file exists
  -g --get-request
  -i --input-json           read json from stdin to send to action
  -I --input=JSONL_INPUT    input json lines from file instead of stdin
  -j --output-json          output plain json instead of pretty-printed json
  -J --output-jsonl         output list responses as json lines instead of
                            pretty-printed json
  -l --log=LOG_FILE         append messages generated to LOG_FILE
  -m --max-records=MAX      exit after processing MAX records
  -n --create-only          create new records, don't update existing records
  -o --update-only          update existing records, don't create new records
  -O --output=JSONL_OUTPUT  output to json lines file instead of stdout
  -p --processes=PROCESSES  set the number of worker processes [default: 1]
  -q --quiet                don't display progress messages
  -r --remote=URL           URL of CKAN server for remote actions
  -s --start-record=START   start from record number START, where the first
                            record is number 1 [default: 1]
  -u --ckan-user=USER       perform actions as user with this name, uses the
                            site sysadmin user when not specified
  -w --worker               launch worker process, used internally by load
                            and dump commands
  -z --gzip                 read/write gzipped data
"""

import sys
from docopt import docopt
from pkg_resources import load_entry_point

from ckanapi.version import __version__
from ckanapi.remoteckan import RemoteCKAN
from ckanapi.localckan import LocalCKAN
from ckanapi.cli.load import load_things
from ckanapi.cli.dump import dump_things
from ckanapi.cli.action import action


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
                url='https://github.com/open-data/ckanapi'),
            get_only=arguments['--get-request'],
            )
    else:
        ckan = LocalCKAN(username=arguments['--ckan-user'])

    if arguments['action']:
        for r in action(ckan, arguments):
            sys.stdout.write(r)
        return

    things = ['datasets', 'groups', 'organizations']
    thing = [x for x in things if arguments[x]]
    if arguments['load']:
        assert len(thing) == 1, thing
        return load_things(ckan, thing[0], arguments)

    if arguments['dump']:
        assert len(thing) == 1, thing
        return dump_things(ckan, thing[0], arguments)

    assert 0, arguments # we shouldn't be here


def _switch_to_paster(arguments):
    """
    With --config we switch to the paster command version of the cli
    """
    sys.argv[1:1] = ["--plugin=ckanapi", "ckanapi"]
    sys.exit(load_entry_point('PasteScript', 'console_scripts', 'paster')())
