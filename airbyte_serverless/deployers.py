import tempfile
import subprocess

import yaml

DOCKERFILE = '''
FROM {docker_image}

RUN pip install airbyte-serverless==0.14

ENV PYTHONUNBUFFERED True

COPY connection.yaml ./connections/connection.yaml

ENTRYPOINT abs run connection --from-deployed-docker-image

'''

def exec(command):
    try:
        print('Executing command >', command)
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        try:
            raise Exception('Error. See Above. ' + e.output.decode(errors='ignore').strip())
        except:
            raise Exception('Error. See Above.')


class BaseDeployer:

    yaml_definition_example = ''

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
        open(f'{self.folder}/connection.yaml', 'w', encoding='utf-8').write(
            self.connection.yaml_config
        )
        dockerfile = DOCKERFILE.format(
            docker_image=self.connection.source.docker_image
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

    yaml_definition_example = '\n'.join([
        'project:  # REQUIRED | string | GCP Project where cloud run job will be deployed',
        'region: "europe-west1" # REQUIRED | string | Region where cloud run job will be deployed',
    ])

    @property
    def deploy_dockerfile_command(self):
        return f'gcloud beta run jobs deploy {self.connection.name} --source={self.folder} --execute-now --wait --project={self.connection.config["deployer"]["config"]["project"]} --region={self.connection.config["deployer"]["config"]["region"]} --max-retries=0'


DEPLOYER_CLASS_MAP = {
    'local_docker': LocalDockerDeployer,
    'cloud_run_job': CloudRunJobDeployer,
}


class Deployer:

    def __init__(self, deployer_type_or_connection):
        if isinstance(deployer_type_or_connection, str):
            connection = None
            self.deployer_type = deployer_type_or_connection
        else:
            connection = deployer_type_or_connection
            self.deployer_type = connection.config.get('deployer', {}).get('type')
            assert self.deployer_type, 'Missing deployer.type field in connection'

        assert self.deployer_type in DEPLOYER_CLASS_MAP, f'deployer_type should be among {list(DEPLOYER_CLASS_MAP.keys())}'
        self.deployer = DEPLOYER_CLASS_MAP[self.deployer_type](connection)
        self.yaml_definition_example = '\n'.join([
            f'type: "{self.deployer_type}" # GENERATED | string | Deployer Type. Must be one of {list(DEPLOYER_CLASS_MAP.keys())}',
            f'config: # PREGENERATED | object | PLEASE UPDATE this pre-generated config',
            '  ' + self.deployer.yaml_definition_example.replace('\n', '\n  '),
        ])    

    def __getattr__(self, name):
        return getattr(self.deployer, name)