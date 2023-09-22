import os
import re
import base64

import yaml
import jinja2

from .sources import Source
from .destinations import Destination
from .deployers import Deployer



CONNECTION_CONFIG_TEMPLATE = jinja2.Template('''
source:
  {{ source.yaml_definition_example | indent(2, False) }}

destination:
  {{ destination.yaml_definition_example | indent(2, False) }}

deployer:
  {{ deployer.yaml_definition_example | indent(2, False) }}
''')


class Connection:
    '''
    A `Connection` instance:
    - instantiates a `source` and a `destination` from provided `yaml_config`
    - has a `run` method to perform extract-load from `source` to `destination`
    '''

    def __init__(self, yaml_config):
        self.yaml_config = yaml_config

    def init_yaml_config(self, source, destination, deployer):
        source = Source(source)
        destination = Destination(destination)
        deployer = Deployer(deployer)
        self.yaml_config = CONNECTION_CONFIG_TEMPLATE.render(
            source=source,
            destination=destination,
            deployer=deployer,
        )

    @property
    def config(self):
        return yaml.safe_load(self.yaml_config) or {}

    def set_streams(self, streams):
        assert streams, '`streams` variable must be defined'
        self.yaml_config = re.sub(r'streams:[^#]*(#*.*)', f'streams: {streams} \g<1>', self.yaml_config)

    @property
    def source(self):
        source_config = self.config.get('source')
        assert source_config, f'yaml_config does not contain a `source` field. Please re-create connection'
        return Source(**source_config)

    @property
    def destination(self):
        destination_config = self.config.get('destination')
        assert destination_config, f'yaml_config does not contain a `destination` field. Please re-create connection'
        return Destination(**destination_config)

    def run(self):
        state = self.destination.get_state()
        messages = self.source.extract(state=state)
        self.destination.load(messages)

    def deploy(self):
        deployer = Deployer(self)
        deployer.deploy_and_run()



class ConnectionFromFile(Connection):
    '''
    A `ConnectionFromFile` extends a `Connection` with
    `yaml_config` stored in a configuration file instead of in a variable
    '''

    CONNECTIONS_FOLDER = 'connections'

    def __init__(self, name):
        self.name = name
        self.config_filename = f'{self.CONNECTIONS_FOLDER}/{self.name}.yaml'

    def init_yaml_config(self, source, destination, deployer):
        assert not self.config, (
            f'Connection `{self.name}` already exists. '
            f'If you want to re-init it, delete the file `{self.config_filename}`'
            ' and run this command again'
        )
        super().init_yaml_config(source, destination, deployer)

    @property
    def yaml_config(self):
        if not os.path.isfile(self.config_filename):
            return ''
        return open(self.config_filename, encoding='utf-8').read()

    @yaml_config.setter
    def yaml_config(self, yaml_config):
        os.makedirs(self.CONNECTIONS_FOLDER, exist_ok=True)
        return open(self.config_filename, 'w', encoding='utf-8').write(yaml_config)

    @classmethod
    def list_connections(cls):
        return [
            filename.replace('.yaml', '')
            for filename in os.listdir(cls.CONNECTIONS_FOLDER)
            if filename.endswith('.yaml')
        ]

class ConnectionFromEnvironementVariables(Connection):

    def __init__(self):
        executable = os.environ.get('AIRBYTE_ENTRYPOINT')
        yaml_config_b64 = os.environ.get('YAML_CONFIG')
        assert executable, 'AIRBYTE_ENTRYPOINT environment variable is not set'
        assert yaml_config, 'YAML_CONFIG environment variable is not set'

        self.yaml_config = base64.b64decode(yaml_config_b64.encode('utf-8')).decode('utf-8')

        yaml.safe_load(self.yaml_config)