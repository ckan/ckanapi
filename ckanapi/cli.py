"""ckanapi command line interface

Usage:
  ckanapi action ACTION_NAME
          [KEY=VALUE ...] [[-c CONFIG] [-u USER] | -r SITE_URL [-a APIKEY]]
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
  -c --config=CONFIG        CKAN configuration file for local actions
                            [default: ./development.ini]
  -u --ckan-user=USER       perform actions as user with this name, uses the
                            site sysadmin user when not specified
  -r --remote=URL           URL of CKAN server for remote actions
  -a --apikey=APIKEY        API key to use for remote actions
  -s --start-record=START   start from record number START [default: 1]
  -m --max-records=MAX      exit after processing MAX records
  -l --log=LOG_FILE         append messages generated to LOG_FILE
  -p --processes=PROCESSES  set the number of worker processes [default: 1]
  -n --create-only          create new records, don't update existing records
  -o --update-only          update existing records, don't create new records
  -q --quiet                don't display progress messages
  -z --gzip                 read/write gzipped data
"""

from docopt import docopt

from ckanapi.version import __version__

def main():
    arguments = docopt(__doc__, version=__version__)
    print(arguments)
