"""
implementation of the action cli command
"""

import sys
import json
from os.path import expanduser

from ckanapi.cli.utils import compact_json, pretty_json
from ckanapi.errors import CLIError


def action(ckan, arguments, stdin=None):
    """
    call an action with KEY=STRING, KEY:JSON or JSON args, yield the result
    """
    if stdin is None:
        stdin = getattr(sys.stdin, 'buffer', sys.stdin)

    file_args = {}
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
            fkey, p, fvalue = kv.partition('@')
            if len(jkey) > len(skey) < len(fkey):
                action_args[skey] = svalue
            elif len(skey) > len(jkey) < len(fkey):
                try:
                    value = json.loads(jvalue)
                except ValueError:
                    raise CLIError("KEY:JSON argument %r has invalid JSON "
                        "value %r" % (jkey, jvalue))
                action_args[jkey] = value
            elif len(jkey) > len(fkey) < len(skey):
                try:
                    f = open(expanduser(fvalue), 'rb')
                except IOError as e:
                    raise CLIError("Error opening %r: %s" %
                        (expanduser(fvalue), e.args[1]))
                file_args[fkey] = f
            else:
                raise CLIError("argument not in the form KEY=STRING, "
                    "KEY:JSON or KEY@FILE %r" % kv)

    def call():
        return ckan.call_action(arguments['ACTION_NAME'], action_args,
                                files=file_args,
                                requests_kwargs=requests_kwargs)

    if arguments['--profile']:
        from cProfile import Profile
        with Profile() as pr:
            result = call()
        pr.dump_stats(arguments['--profile'])
    else:
        result = call()

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
