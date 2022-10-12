import click

@click.command(
    context_settings={'ignore_unknown_options': True},
    short_help='Local API calls with ckanapi tool'
)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def api(context, args):
    from ckanapi.cli.main import main
    import sys
    sys.argv[1:] = args
    context.exit(main(running_with_paster=True) or 0)
