"""
implementation of dump_metadata cli command
"""

import sys
import gzip
import json
from datetime import datetime
import os

from ckanapi.cli.utils import compact_json, \
    quiet_int_pipe, pretty_json

DEFAULT_PAGINATION = 50

def dump_metadata(ckan, arguments, pagination=DEFAULT_PAGINATION,
        stdout=None, stderr=None):
    '''
    Dump all the JSON metadata records.
    This is often a better than using dump_things with thing=datasets,
    as sites like catalog.data.gov do not support package_list api.

    The package_search API is used with pagination.
    '''
    if pagination < 1:
        raise ValueError("Pagination size must be greater or equal to 1")
    if stdout is None:
        stdout = getattr(sys.stdout, 'buffer', sys.stdout)
    if stderr is None:
        stderr = getattr(sys.stderr, 'buffer', sys.stderr)

    jsonl_output = stdout
    if arguments['--output']:
        jsonl_output = open(arguments['--output'], 'wb')
    if arguments['--gzip']:
        jsonl_output = gzip.GzipFile(fileobj=jsonl_output)

    with quiet_int_pipe() as errors:
        count = 0
        total_count = 0
        total_known = False
        while not total_known or total_count > count:
            response = ckan.call_action("package_search", dict(rows=pagination, 
                    start=count, sort="id asc"))
            total_count = response["count"]
            total_known = True
            for record in response["results"]:
                jsonl_output.write(compact_json(record, 
                    sort_keys=True) + b'\n')
                count += 1
    if 'pipe' in errors:
        return 1
    if 'interrupt' in errors:
        return 2

