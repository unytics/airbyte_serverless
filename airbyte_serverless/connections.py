import os

import yaml
import jinja2

from . import sources
from . import airbyte_utils


CONNECTIONS_FOLDER = 'connections'

CONNECTION_CONFIG_TEMPLATE = jinja2.Template('''
source:
  docker_image: {{ source_docker_image }}
  config:
    {{ source_yaml_config | indent(4, False) }}
''')



class Connection:

    def __init__(self, name):
        self.name = name
        self.config_filename = f'{CONNECTIONS_FOLDER}/{self.name}.yaml'

    def init(self, source, destination):
        assert not self.config, (
            f'Connection `{self.name}` already exists. '
            f'If you want to re-init it, delete the file `{self.config_filename}`'
            ' and run this command again'
        )        
        source = sources.DockerAirbyteSource(source)
        source_yaml_config = airbyte_utils.generate_connection_yaml_config_sample(source.spec)
        self.yaml_config = CONNECTION_CONFIG_TEMPLATE.render(
            source_docker_image=source.docker_image,
            source_yaml_config=source_yaml_config
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
        return sources.DockerAirbyteSource(**source_config)

    @property
    def destination(self):
        destination_config= self.config.get('destination')
        assert destination_config, f'File `{self.config_filename}` does not exist or does not contains a `destination` field. Please create or reset the connection'
        return destinations.BigQueryDestination(**destination_config)
    