import tempfile
import subprocess

import yaml

DOCKERFILE = '''
FROM {docker_image}

RUN pip install airbyte-serverless

ENV PYTHONUNBUFFERED True

COPY <<EOF ./connections/connection.yaml
{connection_config}
EOF

ENTRYPOINT echo "salut" && abs run connection --from-deployed-docker-image

'''

class BaseDeployer:
    def __init__(self, connection):
        self.connection = connection
        self.folder_obj = tempfile.TemporaryDirectory()  # Used as clean directory to host Dockerfile to deploy
        self.folder = self.folder_obj.name        

    def deploy(self):
        self._create_dockerfile()
        self._deploy_dockerfile()

    def deploy_and_run(self):
        self.deploy()
        self.run()

    def _create_dockerfile(self):
        dockerfile = DOCKERFILE.format(
            docker_image=self.connection.source.docker_image,
            connection_config=self.connection.yaml_config,
        )
        open(f'{self.folder}/Dockerfile', 'w', encoding='utf-8').write(dockerfile)

    def _deploy_dockerfile(self):
        try:
            return subprocess.check_output(self.deploy_command, shell=True).decode().strip()
        except subprocess.CalledProcessError as e:
            raise Exception('Deploy Error. See Above. ' + e.output.decode(errors='ignore').strip())

    def run(self):
        try:
            return subprocess.check_output(self.run_command, shell=True).decode().strip()
        except subprocess.CalledProcessError as e:
            raise Exception('Run Error. See Above. ' + e.output.decode(errors='ignore').strip())
                
    @property
    def deploy_command(self):
        raise NotImplementedError()

    @property
    def run_command(self):
        raise NotImplementedError()


class LocalDockerDeployer(BaseDeployer):
   
    @property
    def deploy_command(self):
        return f'docker build {self.folder} -t {self.connection.name}'        
        
    @property
    def run_command(self):
        return f'docker run --rm -i {self.connection.name}'   


class CloudRunJobDeployer(BaseDeployer):

    @property
    def deploy_command(self):
        return f'gcloud run jobs deploy {self.connection_name} --source={self.folder} --execute-now --wait --project=bigfunctions --region=europe-west1 --max-retries=0'

