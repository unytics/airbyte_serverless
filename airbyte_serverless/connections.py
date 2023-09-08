import os

import yaml

from . import sources
from . import airbyte_utils


CONNECTIONS_FOLDER = 'connections'


class Connection:

    def __init__(self, name):
        self.name = name
        self.config_filename = f'{CONNECTIONS_FOLDER}/{self.name}.yaml'

    def reset(self, source, destination):
        source = sources.DockerAirbyteSource(source)
        self.yaml_config = airbyte_utils.generate_connection_yaml_config_sample(source.spec)

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
