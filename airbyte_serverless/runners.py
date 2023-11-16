import base64
from google.cloud.run_v2 import Container, EnvVar, ResourceRequirements, CreateJobRequest
import google.cloud.run_v2


class BaseRunner:
    yaml_definition_example = ''

    def __init__(self, connection):
        self.connection = connection

    def run(self):
        raise NotImplementedError()


class DirectRunner(BaseRunner):

    def run(self):
        state = self.connection.destination.get_state()
        messages = self.connection.source.extract(state=state)
        self.connection.destination.load(messages)


class CloudRunJobRunner(BaseRunner):
    yaml_definition_example = '\n'.join([
        'project:  # REQUIRED | string | GCP Project where cloud run job will be deployed',
        'region: "europe-west1" # REQUIRED | string | Region where cloud run job will be deployed',
        'service_account: "" # OPTIONAL | string | Service account email used bu Cloud Run Job. If empty default compute service account will be used',
        'env_vars:  # OPTIONAL | dict | Environements Variables',
    ])

    @staticmethod
    def get_container(docker_image: str, fixed_env_var: EnvVar, external_env_vars: list) -> Container:
        """
        Get the Container object for the Cloud Run job.

        Args:
            docker_image: The Docker image for the container.
            fixed_env_var: Fixed environment variable for the container.
            external_env_vars: List of external environment variables.

        Returns:
            Container: The Container object.
        """
        container = Container()
        container.image = docker_image
        container.name = "gsheet-container"
        container.command = ["/bin/sh"]
        container.args = ['-c', 'pip install airbyte-serverless && abs run-env-vars']
        container.env = [fixed_env_var] + external_env_vars

        resource_limits = {"memory": '512Mi', "cpu": '1'}
        resource_requirements = ResourceRequirements(limits=resource_limits)

        container.resources = resource_requirements

        return container

    @staticmethod
    def get_env_vars(config_env_vars: dict, yaml_config: str) -> tuple[EnvVar, list]:
        """
        Get environment variables for the Cloud Run job.

        Args:
            config_env_vars: Configuration environment variables.
            yaml_config: YAML configuration.

        Returns:
            tuple: Tuple containing fixed and external environment variables.
        """
        env = []
        if config_env_vars:
            assert isinstance(config_env_vars, dict), "Given env_vars argument should be a dict"
            env = [{'name': k, 'value': v} for k, v in config_env_vars.items()]

        ext_env_vars = []
        for e in env:
            env_proto = EnvVar()
            env_proto.name = e["name"]
            env_proto.value = str(e["value"])
            ext_env_vars.append(env_proto)

        fixed_env_vars = EnvVar()
        fixed_env_vars.name = "YAML_CONFIG"
        fixed_env_vars.value = yaml_config

        return fixed_env_vars, ext_env_vars

    @staticmethod
    def get_job_request(
            container: Container,
            service_account: str,
            timeout: str,
            max_retries: int,
            request_parent: str,
            request_job_id: str
    ) -> CreateJobRequest:
        """
         Get the Job request for the Cloud Run job.

         Args:
             container: The Container object.
             service_account: Service account for the job.
             timeout: Timeout for the job.
             max_retries: Maximum retries for the job.
             request_parent: Parent for the job request.
             request_job_id: Job ID for the request.

         Returns:
             The CreateJobRequest object.
         """
        job = google.cloud.run_v2.Job()
        job.template.template.containers = [container]
        job.template.template.timeout = timeout
        job.template.template.max_retries = max_retries
        if service_account:
            job.template.template.service_account = service_account
        job_request = {
            "parent": request_parent,
            "job_id": request_job_id,
            "job": job
        }
        request = CreateJobRequest(job_request)

        return request

    def run(self):
        import google.api_core.exceptions
        cloud_run = google.cloud.run_v2.JobsClient()

        docker_image = self.connection.config['source']['docker_image']
        runner_config = self.connection.config['remote_runner']['config']
        project = runner_config['project']
        region = runner_config['region']
        service_account = runner_config.get('service_account')
        config_env_vars = runner_config.get('env_vars')

        location = f"projects/{project}/locations/{region}"
        job_id = f'abs-{self.connection.name}'.lower().replace('_', '-')
        job_name = f'{location}/jobs/{job_id}'

        yaml_config_b64 = base64.b64encode(self.connection.yaml_config.encode('utf-8')).decode('utf-8')

        fixed_env_vars, ext_env_vars = self.get_env_vars(config_env_vars=config_env_vars, yaml_config=yaml_config_b64)

        container = self.get_container(
            docker_image=docker_image,
            fixed_env_var=fixed_env_vars,
            external_env_vars=ext_env_vars)

        job_request = self.get_job_request(
            container=container,
            service_account=service_account,
            timeout="3600s",
            max_retries=0,
            request_parent=location,
            request_job_id=job_id
        )

        try:
            cloud_run.delete_job(name=job_name).result()
        except google.api_core.exceptions.NotFound:
            pass

        op = cloud_run.create_job(request=job_request)
        op.result()

        operation = cloud_run.run_job({'name': job_name})
        execution_id = operation.metadata.name.split('/')[-1]
        execution_url = f'https://console.cloud.google.com/run/jobs/executions/details/{region}/{execution_id}/logs?project={project}'
        print('Launched Job. See details at', execution_url)
        operation.result()


RUNNER_CLASS_MAP = {
    'direct': DirectRunner,
    'cloud_run_job': CloudRunJobRunner,
}


class Runner:

    def __init__(self, runner_type, connection):
        Runner = RUNNER_CLASS_MAP.get(runner_type)
        assert Runner, f'`runner_type` should be among {list(RUNNER_CLASS_MAP.keys())}'
        self.runner = Runner(connection)
        self.yaml_definition_example = '\n'.join([
            f'type: "{runner_type}" # GENERATED | string | Runner Type. Must be one of {list(RUNNER_CLASS_MAP.keys())}',
            f'config: # PREGENERATED | object | PLEASE UPDATE this pre-generated config',
            '  ' + self.runner.yaml_definition_example.replace('\n', '\n  '),
        ])

    def __getattr__(self, name):
        return getattr(self.runner, name)
