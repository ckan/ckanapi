"""
implementation of the search datasets cli command
"""

import sys
import json
from os.path import expanduser

from ckanapi.cli.utils import compact_json, pretty_json
from ckanapi.errors import CLIError


ROWS_PER_QUERY = 1000  # match hard limit in some versions of ckan


def search_datasets(ckan, arguments, stdin=None, stdout=None, stderr=None):
    """
    call package_search with KEY=STRING, KEY:JSON or JSON args,
    paginate over the results yield the result
    """
    if stdin is None:
        stdin = getattr(sys.stdin, 'buffer', sys.stdin)
    if stdout is None:
        stdout = getattr(sys.__stdout__, 'buffer', sys.__stdout__)
    if stderr is None:
        stderr = getattr(sys.stderr, 'buffer', sys.stderr)

    requests_kwargs = None
    if arguments['--insecure']:
        requests_kwargs = {'verify': False}
    if arguments['--input-json']:
        action_args = json.loads(stdin.read().decode('utf-8'))
    elif arguments['--input']:
        action_args = {}
        with open(expanduser(arguments['--input'])) as in_f:
            action_args = json.loads(
                in_f.read().decode('utf-8') if sys.version_info.major == 2 else in_f.read())
    else:
        action_args = {}
        for kv in arguments['KEY=STRING']:
            if hasattr(kv, 'decode'):
                kv = kv.decode('utf-8')
            skey, p, svalue = kv.partition('=')
            jkey, p, jvalue = kv.partition(':')
            if len(jkey) > len(skey):
                action_args[skey] = svalue
            elif len(skey) > len(jkey):
                try:
                    value = json.loads(jvalue)
                except ValueError:
                    raise CLIError("KEY:JSON argument %r has invalid JSON "
                        "value %r" % (jkey, jvalue))
                action_args[jkey] = value
            else:
                raise CLIError("argument not in the form KEY=STRING, "
                    "or KEY:JSON %r" % kv)

    jsonl_output = stdout
    if arguments['--output']:
        jsonl_output = open(arguments['--output'], 'wb')
    if arguments['--gzip']:
        jsonl_output = gzip.GzipFile(fileobj=jsonl_output)

    start = int(action_args.get('start', 0))
    while True:
        args = action_args
        if 'rows' not in action_args:
            args = dict(action_args, start=start, rows=ROWS_PER_QUERY)
        result = ckan.call_action(
            'package_search',
            args,
            requests_kwargs=requests_kwargs
        )
        rows = result['results']
        for r in rows:
            jsonl_output.write(compact_json(r, sort_keys=True) + b'\n')
        if not rows or 'rows' in action_args:
            break

        start += len(rows)
