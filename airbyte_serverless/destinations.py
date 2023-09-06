import json
import datetime
import uuid


class BaseDestination:

    def __init__(self, **kwargs):
        raise NotImplementedError()

    def get_state(self):
        raise NotImplementedError()

    def get_logs(self):
        raise NotImplementedError()

    def load(self, messages):
        raise NotImplementedError()


class BigQueryDestination(BaseDestination):

    def __init__(self, dataset='', buffer_size_max=10000):
        import google.cloud.bigquery
        assert dataset, 'dataset argument must be defined'
        assert len(dataset.split('.')) == 2, '`BigQueryDestination.dataset` must be like `project.dataset`'
        self.dataset = dataset
        self.project, _ = self.dataset.split('.')
        self.buffer_size_max = buffer_size_max
        self.bigquery = google.cloud.bigquery.Client(project=self.project)
        self.created_tables = []

    def get_state(self):
        import google.api_core.exceptions
        try:
            rows = self.bigquery.query(f'''
                select json_extract(_airbyte_data, '$.data') as state
                from {self.dataset}._airbyte_states
                order by _airbyte_emitted_at desc
                limit 1
            ''').result()
        except google.api_core.exceptions.NotFound:
            return {}
        rows = list(rows)
        return json.loads(rows[0].state) if rows else {}

    def load(self, messages):
        self.job_started_at = datetime.datetime.utcnow().isoformat()
        self.slice_started_at = self.job_started_at
        buffer = []
        stream = None
        for message in messages:
            if message['type'] == 'RECORD':
                new_stream = message['record']['stream']
                if new_stream != stream and stream is not None:
                    self._insert_rows(stream, buffer)
                    buffer = []
                    self.slice_started_at = datetime.datetime.utcnow().isoformat()
                stream = new_stream
                buffer.append(message['record']['data'])
                if len(buffer) > self.buffer_size_max:
                    self._insert_rows(stream, buffer)
                    buffer = []
            elif message['type'] == 'STATE':
                self._insert_rows(stream, buffer)
                buffer = []
                self._insert_rows('_airbyte_states', [message['state']])
                self.slice_started_at = datetime.datetime.utcnow().isoformat()
            elif message['type'] == 'LOG':
                self._insert_rows('_airbyte_logs', [message['log']])
            elif message['type'] == 'TRACE':
                self._insert_rows('_airbyte_logs', [message['trace']])
            else:
                raise NotImplementedError(f'message type {message["type"]} is not managed yet')
        self._insert_rows(stream, buffer)

    def _insert_rows(self, record_type, records):
        if not records:
            return
        table = self._get_table_name_from_record_type(record_type)
        self._create_table_if_needed(table)
        now  = datetime.datetime.utcnow().isoformat()
        records = [
            {
                '_airbyte_ab_id': str(uuid.uuid4()),
                '_airbyte_job_started_at': self.job_started_at,
                '_airbyte_slice_started_at': self.slice_started_at,
                '_airbyte_emitted_at': now,
                '_airbyte_data': json.dumps(record, ensure_ascii=False),
            }
            for record in records
        ]
        errors = self.bigquery.insert_rows_json(f'{self.dataset}.{table}', records)
        if errors:
            raise ValueError(f'Could not insert rows to BigQuery table {table}. Errors: {errors}')

    def _get_table_name_from_record_type(self, record_type):
        if record_type.startswith('_airbyte'):
            return record_type
        return f'_airbyte_raw_{record_type}'

    def _create_table_if_needed(self, table):
        if table in self.created_tables:
            return
        self.bigquery.query(f'''
            create table if not exists {self.dataset}.{table} (
                _airbyte_ab_id string options(description="Record uuid generated at insertion into BigQuery"),
                _airbyte_job_started_at timestamp options(description="Extract-load job start timestamp"),
                _airbyte_slice_started_at timestamp options(description="When incremental mode is used, data records are emitted by chunks a.k.a. slices. At the end of each slice, a state record is emitted to store a checkpoint. This column stores the timestamp when the slice started"),
                _airbyte_emitted_at timestamp options(description="Record ingestion time into BigQuery"),
                _airbyte_data json options(description="Record data as json")
            )
            partition by date(_airbyte_emitted_at)
            options(
                description="{table} records ingested by simple_airbyte"
            )
        ''').result()
        self.created_tables.append(table)