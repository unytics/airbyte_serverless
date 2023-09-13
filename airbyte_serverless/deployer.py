import tempfile
import subprocess

import yaml

DOCKERFILE = '''
FROM {docker_image}

RUN pip install airbyte-serverless

ENV PYTHONUNBUFFERED True

COPY connection.yaml ./connections/connection.yaml

ENTRYPOINT abs run connection

'''

class CloudRunJobDeployer:

    def __init__(self, connection_name, connection_config, deploy_config):
        self.connection_name = connection_name
        self.connection_config = connection_config
        self.deploy_config = deploy_config

    def deploy(self):
        with tempfile.TemporaryDirectory() as folder:
            open(f'{folder}/connection.yaml', 'w', encoding='utf-8').write(
                yaml.dump(self.connection_config)
            ) 
            docker_image = self.connection_config['source']['docker_image']
            dockerfile = DOCKERFILE.format(docker_image=docker_image)
            open(f'{folder}/Dockerfile', 'w', encoding='utf-8').write(
                dockerfile
            )
            try:
                command = f'gcloud run jobs deploy {self.connection_name} --source=. --execute-now --wait'
                return subprocess.check_output(command, shell=True).decode().strip()
            except subprocess.CalledProcessError as e:
                raise Exception('Deploy Error. See Above. ' + e.output.decode(errors='ignore').strip())

