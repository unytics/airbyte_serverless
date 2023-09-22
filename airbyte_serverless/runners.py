

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
    ])

    def run(self):
        import google.cloud.run_v2
        import google.api_core.exceptions
        cloud_run = google.cloud.run_v2.JobsClient()

        runner_config = self.connection.config['remote_runner']['config']
        project = runner_config['project']
        region = runner_config['region']
        location = f"projects/{project}/locations/{region}"
        job_id = f'abs-{self.connection.name}'.lower()
        job_name = f'{location}/jobs/{job_id}'

        container = {
            "image": f'airbyte/source-faker',
            "command": ["/bin/sh"],
            "args": ['-c', 'pip install airbyte-serverless && abs run-from-environment && echo hsssel'],
            "env": [{"name": "YAML_CONFIG", "value": "CnNvdXJjZToKICBkb2NrZXJfaW1hZ2U6ICJhaXJieXRlL3NvdXJjZS1mYWtlcjowLjEuNCIgIyBHRU5FUkFURUQgfCBzdHJpbmcgfCBBIFB1YmxpYyBEb2NrZXIgQWlyYnl0ZSBTb3VyY2UuIEV4YW1wbGU6IGBhaXJieXRlL3NvdXJjZS1mYWtlcjowLjEuNGAuIChzZWUgY29ubmVjdG9ycyBsaXN0IGF0OiAiaHR0cHM6Ly9odWIuZG9ja2VyLmNvbS9zZWFyY2g/cT1haXJieXRlJTJGc291cmNlLSIgKQogIGNvbmZpZzogIyBQUkVHRU5FUkFURUQgfCBvYmplY3QgfCBQTEVBU0UgVVBEQVRFIHRoaXMgcHJlLWdlbmVyYXRlZCBjb25maWcgYnkgZm9sbG93aW5nIHRoZSBkb2N1bWVudGF0aW9uIGh0dHBzOi8vZG9jcy5haXJieXRlLmNvbS9pbnRlZ3JhdGlvbnMvc291cmNlcy9mYWtlcgogICAgY291bnQ6IDEwMDAgIyBSRVFVSVJFRCB8IGludGVnZXIgfCBIb3cgbWFueSB1c2VycyBzaG91bGQgYmUgZ2VuZXJhdGVkIGluIHRvdGFsLiAgVGhpcyBzZXR0aW5nIGRvZXMgbm90IGFwcGx5IHRvIHRoZSBwdXJjaGFzZXMgb3IgcHJvZHVjdHMgc3RyZWFtLgogICAgc2VlZDogLTEgIyBPUFRJT05BTCB8IGludGVnZXIgfCBNYW51YWxseSBjb250cm9sIHRoZSBmYWtlciByYW5kb20gc2VlZCB0byByZXR1cm4gdGhlIHNhbWUgdmFsdWVzIG9uIHN1YnNlcXVlbnQgcnVucyAobGVhdmUgLTEgZm9yIHJhbmRvbSkKICAgIHJlY29yZHNfcGVyX3N5bmM6IDUwMCAjIE9QVElPTkFMIHwgaW50ZWdlciB8IEhvdyBtYW55IGZha2UgcmVjb3JkcyB3aWxsIGJlIHJldHVybmVkIGZvciBlYWNoIHN5bmMsIGZvciBlYWNoIHN0cmVhbT8gIEJ5IGRlZmF1bHQsIGl0IHdpbGwgdGFrZSAyIHN5bmNzIHRvIGNyZWF0ZSB0aGUgcmVxdWVzdGVkIDEwMDAgcmVjb3Jkcy4KICAgIHJlY29yZHNfcGVyX3NsaWNlOiAxMDAgIyBPUFRJT05BTCB8IGludGVnZXIgfCBIb3cgbWFueSBmYWtlIHJlY29yZHMgd2lsbCBiZSBpbiBlYWNoIHBhZ2UgKHN0cmVhbSBzbGljZSksIGJlZm9yZSBhIHN0YXRlIG1lc3NhZ2UgaXMgZW1pdHRlZD8KICBzdHJlYW1zOiAjIE9QVElPTkFMIHwgc3RyaW5nIHwgQ29tbWEtc2VwYXJhdGVkIGxpc3Qgb2Ygc3RyZWFtcyB0byByZXRyaWV2ZS4gSWYgbWlzc2luZywgYWxsIHN0cmVhbXMgYXJlIHJldHJpZXZlZCBmcm9tIHNvdXJjZS4KCmRlc3RpbmF0aW9uOgogIGNvbm5lY3RvcjogInByaW50IiAjIEdFTkVSQVRFRCB8IHN0cmluZyB8IEFuIEFpcmJ5dGVTZXJ2ZXJsZXNzIERlc3RpbmF0aW9uIENvbm5lY3Rvci4gTXVzdCBiZSBvbmUgb2YgWydwcmludCcsICdiaWdxdWVyeSddCiAgY29uZmlnOiAjIFBSRUdFTkVSQVRFRCB8IG9iamVjdCB8IFBMRUFTRSBVUERBVEUgdGhpcyBwcmUtZ2VuZXJhdGVkIGNvbmZpZwogICAgYnVmZmVyX3NpemVfbWF4OiAxMDAwMCAjIE9QVElPTkFMIHwgaW50ZWdlciB8IG1heGltdW0gbnVtYmVyIG9mIHJlY29yZHMgaW4gYnVmZmVyIGJlZm9yZSB3cml0aW5nIHRvIGRlc3RpbmF0aW9uIChkZWZhdWx0cyB0byAxMDAwMCB3aGVuIG5vdCBzcGVjaWZpZWQpCgpkZXBsb3llcjoKICB0eXBlOiAiY2xvdWRfcnVuX2pvYiIgIyBHRU5FUkFURUQgfCBzdHJpbmcgfCBEZXBsb3llciBUeXBlLiBNdXN0IGJlIG9uZSBvZiBbJ2xvY2FsX2RvY2tlcicsICdjbG91ZF9ydW5fam9iJ10KICBjb25maWc6ICMgUFJFR0VORVJBVEVEIHwgb2JqZWN0IHwgUExFQVNFIFVQREFURSB0aGlzIHByZS1nZW5lcmF0ZWQgY29uZmlnCiAgICBwcm9qZWN0OiAgIyBSRVFVSVJFRCB8IHN0cmluZyB8IEdDUCBQcm9qZWN0IHdoZXJlIGNsb3VkIHJ1biBqb2Igd2lsbCBiZSBkZXBsb3llZAogICAgcmVnaW9uOiAiZXVyb3BlLXdlc3QxIiAjIFJFUVVJUkVEIHwgc3RyaW5nIHwgUmVnaW9uIHdoZXJlIGNsb3VkIHJ1biBqb2Igd2lsbCBiZSBkZXBsb3llZA=="}],
            "resources": {
                "limits": {
                    "memory": '512Mi',
                    "cpu": '1',
                }
            }
        }
        job_config = {
            "containers": [container],
            # "service_account": ,
            # "vpc_access": {
            #   "connector": f'{self.base_job_name}/connectors/functions-connector',
            #   "egress": 1,
            # }
            "timeout": "3600s",
            "max_retries": 0,
        }
        try:
            cloud_run.delete_job(name=job_name).result()
        except google.api_core.exceptions.NotFound:
            pass
        cloud_run.create_job(
            job={'template': {'template': job_config}},
            job_id=job_id,
            parent=location,
        ).result()
        operation = cloud_run.run_job({'name': job_name})
        execution_id = operation.metadata.name.split('/')[-1]
        execution_url = f'https://console.cloud.google.com/run/jobs/executions/details/{region}/{execution_id}/logs?project={project}'
        print('Launched Job. See details at', execution_url)
        result = operation.result()
        print(result)


RUNNER_CLASS_MAP = {
    'direct': DirectRunner,
    'cloud_run_job': CloudRunJobRunner,
    # 'direct': DirectRunner,
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