import functools
import sys
import shutil

import click
from click_help_colors import HelpColorsGroup

from .connections import Connection



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


def handle_error(f):

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            click.echo(click.style(f'ERROR: {e}', fg='red'))
            sys.exit()

    return wrapper




@cli.command()
@click.argument('connection')
@click.option('--source', default='airbyte/source-faker:0.1.4', help='Any Public Docker Airbyte Source. Example: `airbyte/source-faker:0.1.4`. (connectors list: https://hub.docker.com/search?q=airbyte%2Fsource-')
@click.option('--destination', default='print', help='One of `print` or `bigquer:YOUR_PROJECT.YOUR_DATASET`')
@handle_error
def create(connection, source, destination):
    '''
    Create CONNECTION
    '''
    connection = Connection(connection)
    connection.init(source, destination)
    print_success(connection.config)


@cli.command()
@click.argument('connection')
@handle_error
def list_streams(connection):
    '''
    List streams of CONNECTION
    '''
    connection = Connection(connection)
    print_success(connection.source.streams)