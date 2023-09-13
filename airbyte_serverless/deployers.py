import tempfile
import subprocess

import yaml

DOCKERFILE = '''
FROM {docker_image}

RUN pip install airbyte-serverless==0.14

ENV PYTHONUNBUFFERED True

COPY <<EOF ./connections/connection.yaml
{connection_config}
EOF

ENTRYPOINT echo "salut" && abs run connection --from-deployed-docker-image

'''

def exec(command):
    try:
        print('Executing command >', command)
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise Exception('Error. See Above. ' + e.output.decode(errors='ignore').strip())


class BaseDeployer:
    def __init__(self, connection):
        self.connection = connection
        self.folder_obj = tempfile.TemporaryDirectory()  # Used as clean directory to host Dockerfile to deploy
        self.folder = self.folder_obj.name        

    def deploy(self):
        self.create_dockerfile()
        self.deploy_dockerfile()

    def deploy_and_run(self):
        self.deploy()
        self.run()

    def create_dockerfile(self):
        dockerfile = DOCKERFILE.format(
            docker_image=self.connection.source.docker_image,
            connection_config=self.connection.yaml_config,
        )
        open(f'{self.folder}/Dockerfile', 'w', encoding='utf-8').write(dockerfile)

    def deploy_dockerfile(self):
        exec(self.deploy_dockerfile_command)

    def run(self):
        exec(self.run_command)

    @property
    def deploy_dockerfile_command(self):
        raise NotImplementedError()

    @property
    def run_command(self):
        raise NotImplementedError()


class LocalDockerDeployer(BaseDeployer):
   
    @property
    def deploy_dockerfile_command(self):
        return f'docker build {self.folder} -t {self.connection.name}'        
        
    @property
    def run_command(self):
        return f'docker run --rm -i {self.connection.name}'   


class CloudRunJobDeployer(BaseDeployer):

    @property
    def deploy_dockerfile_command(self):
        return f'gcloud run jobs deploy {self.connection_name} --source={self.folder} --execute-now --wait --project=bigfunctions --region=europe-west1 --max-retries=0'

