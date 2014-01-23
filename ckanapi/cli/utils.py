"""
useful bits of code not tied to ckanapi in any way
"""

import time

PYTHON2 = str is bytes
if PYTHON2:
    # we need indent= and sort_keys=
    import simplejson as json
else:
    import json
from contextlib import contextmanager


def completion_stats(window=1):
    """
    Generate completions/second reports on each iteration.

    window - window size for completion reports
    """
    stamps = []
    while True:
        stamps.append(time.time())
        if len(stamps) < window + 1:
            yield '---'
        else:
            yield '%4.2fs' % ((stamps[-1] - stamps[0]) / window)
            stamps = stamps[-window:]


@contextmanager
def quiet_int_pipe():
    """
    let pipe errors and KeyboardIterrupt exceptions cause silent exit
    """
    try:
        yield
    except KeyboardInterrupt:
        pass
    except IOError as e:
        if e.errno != 32:
            raise


def compact_json(r):
    """
    JSON as small as we can make it, with UTF-8
    """
    return json.dumps(r, ensure_ascii=False, separators=(',', ':'))


def pretty_json(r):
    """
    legible sorted JSON, with UTF-8
    """
    return json.dumps(r, ensure_ascii=False, separators=(',', ': '),
        indent=2, sort_keys=True)


