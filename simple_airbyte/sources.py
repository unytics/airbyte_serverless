import tempfile
import subprocess
import json

from . import airbyte_utils


class AirbyteSourceException(Exception):
    pass


class AirbyteSource:

    def __init__(self, exec, config=None, configured_catalog=None):
        self.exec = exec
        self.config = config
        self._configured_catalog = configured_catalog

    def _run(self, action):
        with tempfile.TemporaryDirectory() as temp_dir:
            command = f'{self.exec} {action}'
            needs_config = (action != 'spec')
            if needs_config:
                assert self.config, 'config attribute is not defined'
                filename = f'{temp_dir}/config.json'
                json.dump(self.config, open(filename, 'w', encoding='utf-8'))
                command += f' --config {filename}'
            needs_configured_catalog = (action == 'read')
            if needs_configured_catalog:
                filename = f'{temp_dir}/catalog.json'
                json.dump(self.configured_catalog, open(filename, 'w', encoding='utf-8'))
                command += f' --catalog {filename}'
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            for line in iter(process.stdout.readline, b""):
                content = line.decode().strip()
                message = json.loads(content)
                if message.get('trace', {}).get('error'):
                    raise AirbyteSourceException(json.dumps(message['trace']['error']))
                yield message

    def _run_and_return_first_message(self, action):
        messages = self._run(action)
        message = next(
            (message for message in messages if message['type'] not in ['LOG', 'TRACE']),
            None
        )
        assert message is not None, f'No message returned by AirbyteSource with action `{action}`'
        return message

    @property
    def spec(self):
        message = self._run_and_return_first_message('spec')
        return message['spec']

    @property
    def config_spec(self):
        spec = self.spec
        return spec['connectionSpecification']

    @property
    def documentation_url(self):
        spec = self.spec
        return spec['documentationUrl']

    @property
    def sample_config(self):
        spec = self.spec
        return airbyte_utils.generate_connection_yaml_config_sample(spec)

    @property
    def catalog(self):
        message = self._run_and_return_first_message('discover')
        return message['catalog']

    @property
    def sample_configured_catalog(self):
        catalog = self.catalog
        catalog['streams'] = [
            {
                "stream": stream,
                "sync_mode": "incremental" if 'incremental' in stream['supported_sync_modes'] else 'full_refresh',
                "destination_sync_mode": "append",
                "cursor_field": stream.get('default_cursor_field', [])
            }
            for stream in catalog['streams']
        ]
        return catalog

    @property
    def configured_catalog(self):
        return self._configured_catalog or self.sample_configured_catalog

    @property
    def streams(self):
        return [stream['name'] for stream in self.catalog['streams']]

    @property
    def connection_status(self):
        message = self._run_and_return_first_message('check')
        return message['connectionStatus']

    @property
    def first_message(self):
        message = self._run_and_return_first_message('read')
        return message['record']

    def read(self):
        return self._run('read')
