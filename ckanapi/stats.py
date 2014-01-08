import time

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
