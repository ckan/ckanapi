import sys
from ckan.lib.cli import CkanCommand

from ckanapi import cli

class CKANAPICommand(CkanCommand):
    summary = cli.__doc__.split('\n')[0]
    usage = cli.__doc__

    def command(self):
        assert sys.argv[1] == 'ckanapi', sys.argv
        del sys.argv[1]
        cli.main(running_with_paster=True)
