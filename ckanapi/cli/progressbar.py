# _*_ coding: utf-8 _*_

"""
Implements the progress bar for use in
ckanapi.cli.action:action(RemoteCKAN, resource_create, ...)
"""

from clint.textui.progress import Bar

def mkprogress(encoder):
    """
    Returns a function that can be used as a callback for
    :class:`requests_toolbelt.MultipartEncoderMonitor`.
    :param encoder: instance of :class:`requests_toolbelt.MultipartEncoder`
    """
    expected_size = encoder.len
    bar = Bar(expected_size=expected_size, filled_char = '=')
    waiting = [False]

    def callback(monitor):
        """
        prints progess bar
        :param monitor: instance of
            :class:`requests_toolbelt.MultipartEncoderMonitor`
        """
        if monitor.bytes_read < expected_size:
            bar.show(monitor.bytes_read)
        elif not waiting[0]:
            waiting[0] = True
            print ('\nwaiting for server-side processing ...')

    return callback