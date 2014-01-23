"""
implementation of the action cli command
"""

from ckanapi.cli.utils import compact_json, pretty_json


def action(ckan, arguments):
    """
    call an action with KEY=VALUE args, yield the result
    """
    action_args = {}
    for kv in arguments['KEY=VALUE']:
        key, p, value = kv.partition('=')
        action_args[key] = value
    result = ckan.call_action(arguments['ACTION_NAME'], action_args)

    if arguments['--jsonl']:
        if isinstance(result, list):
            for r in result:
                yield compact_json(r) + '\n'
        else:
            yield compact_json(result) + '\n'
    elif arguments['--plain-json']:
        yield compact_json(result) + '\n'
    else:
        yield pretty_json(result) + '\n'
