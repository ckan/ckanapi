"""
implementation of the action cli command
"""

import sys
import json
from ckanapi.cli.utils import compact_json, pretty_json
from ckanapi.errors import CLIError


def action(ckan, arguments, stdin=None):
    """
    call an action with KEY=STRING, KEY:JSON or JSON args, yield the result
    """
    if stdin is None:
        stdin = getattr(sys.stdin, 'buffer', sys.stdin)

    if arguments['--input-json']:
        action_args = json.loads(stdin.read().decode('utf-8'))
    elif arguments['--input']:
        action_args = json.loads(open(
            arguments['--input']).read().decode('utf-8'))
    else:
        action_args = {}
        for kv in arguments['KEY=STRING']:
            skey, p, svalue = kv.partition('=')
            jkey, p, jvalue = kv.partition(':')
            if len(skey) < len(jkey):
                action_args[skey] = svalue
                continue
            if len(jkey) < len(skey):
                try:
                    value = json.loads(jvalue)
                except ValueError:
                    raise CLIError("KEY:JSON argument %r has invalid JSON "
                        "value %r" % (jkey, jvalue))
                action_args[jkey] = value
                continue
            raise CLIError("argument not in the form KEY=STRING or KEY:JSON "
                "%r" % kv)

    result = ckan.call_action(arguments['ACTION_NAME'], action_args)

    if arguments['--output-jsonl']:
        if isinstance(result, list):
            for r in result:
                yield compact_json(r) + b'\n'
        else:
            yield compact_json(result) + b'\n'
    elif arguments['--output-json']:
        yield compact_json(result) + b'\n'
    else:
        yield pretty_json(result) + b'\n'
