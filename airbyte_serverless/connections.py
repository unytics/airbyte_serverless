import os

from . import sources

CONNECTIONS_FOLDER = 'connections'


class Connection:

    def __init__(self, name):
        self.name = name
        self.config_filename = f'{CONNECTIONS_FOLDER}/{self.name}.yaml'

    def reset(self, source, destination):
        source = sources.DockerAirbyteSource(source)
        self.config = source.config

    @property
    def config(self):
        try:
            return open(self.config_filename, encoding='utf-8').read()
        except:
            pass

    @config.setter
    def config(self, config):
        os.makedirs(CONNECTIONS_FOLDER, exist_ok=True)
        return open(self.config_filename, 'w', encoding='utf-8').write(config)
