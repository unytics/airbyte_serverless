import tempfile
import subprocess
import json

from . import airbyte_utils


class AirbyteSource:

    def __init__(self, exec):
        self.exec = exec

    def run(self, args, catalog=None):
        with tempfile.TemporaryDirectory() as temp_dir:
            command = f'{self.exec} {args}'
            needs_config = 'spec' not in args
            if needs_config:
                filename = f'{temp_dir}/config.json'
                json.dump(self.config, open(filename, 'w', encoding='utf-8'))
                command += f' --config {filename}'
            if catalog:
                filename = f'{temp_dir}/catalog.json'
                json.dump(catalog, open(filename, 'w', encoding='utf-8'))
                command += f' --catalog {filename}'
            print(command)
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            for line in iter(process.stdout.readline, b""):
                content = line.decode().strip()
                message = json.loads(content)
                yield message

    def run_and_return_first_message(self, command):
        messages = self.run(command)
        return next(messages)

    def init_config(self):
        spec = self.spec
        yaml_config = airbyte_utils.generate_connection_yaml_config_sample(spec)
        return yaml_config

    @property
    def spec(self):
        message = self.run_and_return_first_message('spec')
        return message['spec']

    @property
    def catalog(self):
        message = self.run_and_return_first_message('discover')
        return message['catalog']

    @property
    def configured_catalog(self):
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
    def streams(self):
        return [stream['name'] for stream in self.catalog['streams']]

    def check(self):
        message = self.run_and_return_first_message('check')
        return message['connectionStatus']