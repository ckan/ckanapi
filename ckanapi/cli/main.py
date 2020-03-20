"""ckanapi command line interface

Usage:
  ckanapi action ACTION_NAME
          [(KEY=STRING | KEY:JSON | KEY@FILE ) ... | -i | -I JSON_INPUT]
          [-j | -J]
          [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY] [-g] [--insecure]]
  ckanapi load datasets
          [--upload-resources] [-I JSONL_INPUT] [-s START] [-m MAX]
          [-p PROCESSES] [-l LOG_FILE] [-n | -o] [-qwz]
          [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY] [--insecure]]
  ckanapi load (groups | organizations)
          [--upload-logo] [-I JSONL_INPUT] [-s START] [-m MAX]
          [-p PROCESSES] [-l LOG_FILE] [-n | -o] [-qwz]
          [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY] [--insecure]]
  ckanapi load (users | related)
          [-I JSONL_INPUT] [-s START] [-m MAX] [-p PROCESSES] [-l LOG_FILE]
          [-n | -o] [-qwz]
          [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY] [--insecure]]
  ckanapi dump (datasets | groups | organizations | users | related)
          (ID_OR_NAME ... | --all) ([-O JSONL_OUTPUT] | [-D DIRECTORY])
          [-p PROCESSES] [-dqwz]
          [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY] [-g] [--insecure]]
  ckanapi search datasets
          [(KEY=STRING | KEY:JSON ) ... | -i | -I JSON_INPUT]
          [-O JSONL_OUTPUT] [-z]
          [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY] [-g] [--insecure]]
  ckanapi delete (datasets | groups | organizations | users | related)
          (ID_OR_NAME ... | [-I JSONL_INPUT] [-s START] [-m MAX])
          [-p PROCESSES] [-l LOG_FILE] [-qwz]
          [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY] [--insecure]]
  ckanapi (-h | --help)
  ckanapi --version

Options:
  -h --help                 show this screen
  --version                 show version
  -a --apikey=APIKEY        API key to use for remote actions
  --all                     all the things
  -c --config=CONFIG        CKAN configuration file for local actions,
                            defaults to ./development.ini if that file exists
  -g --get-request          use GET instead of POST for API calls
  -i --input-json           read json from stdin to send to action
  -I --input=INPUT          input json/ json lines from file instead of stdin
  -j --output-json          output plain json instead of pretty-printed json
  -J --output-jsonl         output list responses as json lines instead of
                            pretty-printed json
  -d --datastore-fields     export datastore field information along with
                            resource metadata as datastore_fields lists
  -D --datapackages=DIR     download resources and output as datapackages
                            in DIR instead of metadata-only json lines
  -l --log=LOG_FILE         append messages generated to LOG_FILE
  -m --max-records=MAX      exit after processing MAX records
  -n --create-only          create new records, don't update existing records
  --insecure                ignore verifying the SSL certificate for sites
                            using https
  -o --update-only          update existing records, don't create new records
  -O --output=JSONL_OUTPUT  output to json lines file instead of stdout
  -p --processes=PROCESSES  set the number of worker processes [default: 1]
  -q --quiet                don't display progress messages
  -r --remote=URL           URL of CKAN server for remote actions
  -s --start-record=START   start from record number START, where the first
                            record is number 1 [default: 1]
  -u --ckan-user=USER       perform actions as user with this name, uses the
                            site sysadmin user when not specified
  --upload-logo             upload logo image of a group/organization if the
                            image is stored in the original server, otherwise
                            its image url will be used
  --upload-resources        upload resources of a dataset that were uploaded to
                            server. Resources originally linked by external
                            urls will keep the urls,will not be uploaded
  -w --worker               launch worker process, used internally by load
                            and dump commands
  -z --gzip                 read/write gzipped data
"""

import sys
import os
from docopt import docopt
from pkg_resources import load_entry_point

from ckanapi.version import __version__
from ckanapi.remoteckan import RemoteCKAN
from ckanapi.localckan import LocalCKAN
from ckanapi.errors import CLIError
from ckanapi.cli.load import load_things
from ckanapi.cli.dump import dump_things
from ckanapi.cli.delete import delete_things
from ckanapi.cli.action import action
from ckanapi.cli.search import search_datasets


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

    stdout = getattr(sys.stdout, 'buffer', sys.stdout)
    if arguments['action']:
        try:
            for r in action(ckan, arguments):
                stdout.write(r)
            return
        except CLIError as e:
            sys.stderr.write(e.args[0] + '\n')
            return 1

    things = ['datasets', 'groups', 'organizations', 'users', 'related']
    thing = [x for x in things if arguments[x]]
    if (arguments['load'] or arguments['dump'] or arguments['delete']
            ) and arguments['--processes'] != '1' and os.name == 'nt':
        sys.stderr.write(
            "multiple worker processes are not supported on windows\n")
        arguments['--processes'] = '1'

    if arguments['load']:
        return load_things(ckan, thing[0], arguments)

    if arguments['dump']:
        return dump_things(ckan, thing[0], arguments)

    if arguments['delete']:
        return delete_things(ckan, thing[0], arguments)

    if arguments['search']:
        return search_datasets(ckan, arguments)

    assert 0, arguments # we shouldn't be here


def _switch_to_paster(arguments):
    """
    With --config we switch to the paster command version of the cli
    """
    sys.argv[1:1] = ["--plugin=ckanapi", "ckanapi"]
    sys.exit(load_entry_point('PasteScript', 'console_scripts', 'paster')())
