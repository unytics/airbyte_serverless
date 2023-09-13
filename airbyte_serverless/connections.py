import os

import yaml
import jinja2

from .sources import Source
from .destinations import Destination


CONNECTIONS_FOLDER = 'connections'

CONNECTION_CONFIG_TEMPLATE = jinja2.Template('''
source:
  {{ source.yaml_definition_example | indent(2, False) }}
destination:
  {{ destination.yaml_definition_example | indent(2, False) }}
''')


def list_connections():
    return [
        filename.replace('.yaml', '')
        for filename in os.listdir(CONNECTIONS_FOLDER)
        if filename.endswith('.yaml')
    ]


class Connection:

    def __init__(self, name, is_deployed=False):
        self.name = name
        self.config_filename = f'{CONNECTIONS_FOLDER}/{self.name}.yaml'
        self.is_deployed = is_deployed

    def init(self, source, destination):
        assert not self.config, (
            f'Connection `{self.name}` already exists. '
            f'If you want to re-init it, delete the file `{self.config_filename}`'
            ' and run this command again'
        )
        source = Source(source)
        destination = Destination(destination)
        self.yaml_config = CONNECTION_CONFIG_TEMPLATE.render(
            source=source,
            destination=destination
        )

    @property
    def yaml_config(self):
        if not os.path.isfile(self.config_filename):
            return ''
        return open(self.config_filename, encoding='utf-8').read()

    @yaml_config.setter
    def yaml_config(self, yaml_config):
        os.makedirs(CONNECTIONS_FOLDER, exist_ok=True)
        return open(self.config_filename, 'w', encoding='utf-8').write(yaml_config)

    @property
    def config(self):
        return yaml.safe_load(self.yaml_config) or {}

    @property
    def source(self):
        source_config= self.config.get('source')
        assert source_config, f'File `{self.config_filename}` does not exist or does not contains a `source` field. Please create or reset the connection'
        return Source(**source_config, is_deployed=self.is_deployed)

    @property
    def destination(self):
        destination_config= self.config.get('destination')
        assert destination_config, f'File `{self.config_filename}` does not exist or does not contains a `destination` field. Please create or reset the connection'
        return Destination(**destination_config)

    def run(self):
        state = self.destination.get_state()
        messages = self.source.extract(state=state)
        self.destination.load(messages)
