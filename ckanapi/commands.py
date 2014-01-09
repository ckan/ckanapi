import sys
from ckan.lib.cli import CkanCommand

from ckanapi import cli

class _IgnoredOptions(object):
    pass

class _DelegateParsing(object):
    usage = cli.__doc__

    def parse_args(self, args):
        assert sys.argv[1] == 'ckanapi', sys.argv
        del sys.argv[1]
        arguments = cli.parse_arguments()
        options = _IgnoredOptions()
        cfg = arguments['--config']
        options.config = cfg if cfg is not None else './development.ini'
        return options, []

class CKANAPICommand(CkanCommand):
    summary = cli.__doc__.split('\n')[0]
    usage = cli.__doc__
    parser = _DelegateParsing()

    def command(self):
        self._load_config()

        cli.main(running_with_paster=True)
