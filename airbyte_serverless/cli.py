import click
from click_help_colors import HelpColorsGroup

from . import sources
from . import destinations


CONNECTIONS_FOLDER = 'connections'


@click.group(
    cls=HelpColorsGroup,
    help_headers_color='yellow',
    help_options_color='cyan'
)
def cli():
    pass


@cli.command()
@click.argument('connection')
@click.option('--source', default='airbyte/source-faker:0.1.4', help='Any Public Docker Airbyte Source. Example: `airbyte/source-faker:0.1.4`. (connectors list: https://hub.docker.com/search?q=airbyte%2Fsource-')
@click.option('--destination', default='print', help='One of `print` or `bigquer:YOUR_PROJECT.YOUR_DATASET`')
def create(connection, source, destination):
    '''
    Create CONNECTION
    '''
    print('hello')
