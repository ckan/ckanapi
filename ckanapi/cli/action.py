"""
implementation of the action cli command
"""

import sys
import json
from ckanapi.cli.utils import compact_json, pretty_json


def action(ckan, arguments,
        stdin=None):
    """
    call an action with KEY=VALUE args, yield the result
    """
    if stdin is None:
        stdin = getattr(sys.stdin, 'buffer', sys.stdin)

    if arguments['--stdin-json']:
        action_args = json.loads(stdin.read().decode('utf-8'))
    else:
        action_args = {}
        for kv in arguments['KEY=VALUE']:
            key, p, value = kv.partition('=')
            action_args[key] = value
    result = ckan.call_action(arguments['ACTION_NAME'], action_args)

    if arguments['--jsonl']:
        if isinstance(result, list):
            for r in result:
                yield compact_json(r) + b'\n'
        else:
            yield compact_json(result) + b'\n'
    elif arguments['--plain-json']:
        yield compact_json(result) + b'\n'
    else:
        yield pretty_json(result) + b'\n'
