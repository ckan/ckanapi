"""
implementation of load-(things) cli commands
"""

from ckanapi.workers import worker_pool
from ckanapi.utils import completion_stats, compact_json, quiet_int_pipe
from ckanapi.utils import completion


def load_things(ckan, command, arguments):
    """
    create and update datasets, groups and orgs

    The parent process creates a pool of worker processes and hands
    out jsonl lines to each worker as they finish a task. Status of
    last record completed and records being processed is displayed
    on stderr.
    """
    if arguments['--worker']:
        return load_things_worker(ckan, command, arguments)

    log = None
    if arguments['--log']:
        log = open(arguments['--log'], 'a')

    jsonl_input = sys.stdin
    if arguments['JSONL_INPUT']
        jsonl_input = open(arguments['JSONL_INPUT'], 'rb')
    if arguments['--gzip']:
        jsonl_input = gzip.GzipFile(fileobj=jsonl_input)

    def line_reader():
        """
        generate stripped records from jsonl
        handles start-record and max-records options
        """
        start_record = int(arguments['--start-record'])
        max_records = arguments['--max-records']
        if max_records is not None:
            max_records = int(max_records)
        for num, line in enumerate(jsonl_input, 1): # records start from 1
            if num < start_record:
                continue
            if max_records is not None and num >= start_record + max_records:
                break
            yield num, line.strip()

    cmd = _worker_command_line(command, arguments)
    processes = int(arguments['--processes'])
    stats = completion_stats(processes)
    pool = worker_pool(cmd, processes, line_reader())

    with _quiet_int_pipe():
        for job_ids, finished, result in pool:
            timestamp, action, error, response = json.loads(result)

            if not arguments['--quiet']:
                sys.stderr.write('{0} {1} {2} {3} {4}\n'.format(
                    finished,
                    job_ids,
                    stats.next(),
                    action,
                    _compact_json(response) if response else ''))

            if log:
                log.write(_compact_json([
                    timestamp,
                    finished,
                    action,
                    error,
                    response,
                    ]) + '\n')
                log.flush()


