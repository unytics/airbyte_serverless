import traceback
import functools
import sys
import shutil

import click
from click_help_colors import HelpColorsGroup

from .sources import AirbyteSourceException
from .connections import ConnectionFromFile, ConnectionFromEnvironementVariables



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
        except (AssertionError, AirbyteSourceException) as e:
            click.echo(click.style(f'ERROR: {e}', fg='red'))
            sys.exit()
        except Exception as e:
            click.echo(click.style(f'ERROR: {e}', fg='red'))
            print(traceback.format_exc())
            sys.exit()

    return wrapper




@cli.command()
@click.argument('connection')
@click.option('--source', default='airbyte/source-faker:0.1.4', help='Any Public Docker Airbyte Source. Example: `airbyte/source-faker:0.1.4`. (see connectors list at: "https://hub.docker.com/search?q=airbyte%2Fsource-" )')
@click.option('--destination', default='print', help='One of `print` or `bigquery`')
@click.option('--deployer', default='cloud_run_job', help='One of `local_docker` or `cloud_run_job`')
@handle_error
def create(connection, source, destination, deployer):
    '''
    Create CONNECTION
    '''
    connection = ConnectionFromFile(connection)
    connection.init_yaml_config(source, destination, deployer)
    print_success(f'Created connection `{connection.name}` with source `{source}` and destination `{destination}` and deployer `{deployer}`')


@cli.command()
@handle_error
def list():
    '''
    List created connections
    '''
    print_success(
        'Configured Connections are:\n' +
        '\n'.join([f'- {connection}' for connection in ConnectionFromFile.list_connections() or ['NONE']])
    )

@cli.command()
@click.argument('connection')
@handle_error
def list_available_streams(connection):
    '''
    List available streams of CONNECTION
    '''
    connection = ConnectionFromFile(connection)
    print_success(','.join(connection.source.available_streams))


@cli.command()
@click.argument('connection')
@click.argument('streams')
@handle_error
def set_streams(connection, streams):
    '''
    Set STREAMS to retrieve for CONNECTION (STREAMS is a comma-separated list of streams given by `list-available-streams` command)
    '''
    connection = ConnectionFromFile(connection)
    connection.set_streams(streams)
    print_success(f'Successfully set streams {streams} of connection {connection.name}')


@cli.command()
@click.argument('connection')
@handle_error
def run(connection):
    '''
    Run Extract-Load for CONNECTION
    '''
    connection = ConnectionFromFile(connection)
    connection.run()
    print_success('OK')


@cli.command()
@handle_error
def run_from_environment():
    '''
    Run Extract-Load for CONNECTION defined by AIRBYTE_ENTRYPOINT 
    and AIRBYTE_CONFIG environment variables
    '''
    connection = ConnectionFromEnvironementVariables()
    connection.run()
    print_success('OK')


@cli.command()
@click.argument('connection')
@handle_error
def deploy(connection):
    '''
    Deploy CONNECTION
    '''
    connection = ConnectionFromFile(connection)
    connection.deploy()
    print_success('OK')