import sys
import shutil

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


def print_color(msg):
    click.echo(click.style(msg, fg='cyan'))

def print_success(msg):
    click.echo(click.style(f'SUCCESS: {msg}', fg='green'))

def print_info(msg):
    click.echo(click.style(f'INFO: {msg}', fg='yellow'))

def print_command(msg):
    click.echo(click.style(f'INFO: `{msg}`', fg='magenta'))

def print_warning(msg):
    click.echo(click.style(f'WARNING: {msg}', fg='cyan'))

def handle_error(msg):
    click.echo(click.style(f'ERROR: {msg}', fg='red'))
    sys.exit()


@cli.command()
@click.argument('connection')
@click.option('--source', default='airbyte/source-faker:0.1.4', help='Any Public Docker Airbyte Source. Example: `airbyte/source-faker:0.1.4`. (connectors list: https://hub.docker.com/search?q=airbyte%2Fsource-')
@click.option('--destination', default='print', help='One of `print` or `bigquer:YOUR_PROJECT.YOUR_DATASET`')
def create(connection, source, destination):
    '''
    Create CONNECTION
    '''
    if shutil.which('docker') is None:
        handle_error('`docker` is not installed')
    source = sources.AirbyteSource(source)
    print(source.config)
