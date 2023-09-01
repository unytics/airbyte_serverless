import json
import datetime
import uuid



class BaseDestination:

    def __init__(self, catalog):
        self.catalog = catalog
        self.streams = [s['stream']['name'] for s in catalog['streams']]

    def get_state(self):
        raise NotImplementedError()

    def get_logs(self):
        raise NotImplementedError()

    def load(self, messages):
        raise NotImplementedError()


class BigQueryDestination(BaseDestination):

    def __init__(self, catalog, dataset='', buffer_size_max=10000):
        assert dataset, 'dataset argument must be defined'
        try:
            project, _ = dataset.split('.')
        except:
            assert False, '`BigQueryDestination.dataset` must be like `project.dataset`'

        super().__init__(catalog)
        self.dataset = dataset
        self.buffer_size_max = buffer_size_max
        self.tables = {
            **{
                'airbyte_logs': '_airbyte_logs',
                'airbyte_states': '_airbyte_states',
            },
            **{
                stream: f'_airbyte_raw_{stream}'
                for stream in self.streams
            },
        }
        create_table_query = '''
            create table if not exists `{dataset}.{table}` (
                _airbyte_ab_id string options(description="Record uuid generated at insertion into BigQuery"),
                _airbyte_job_started_at timestamp options(description="Extract-load job start timestamp"),
                _airbyte_slice_started_at timestamp options(description="When incremental mode is used, data records are emitted by chunks a.k.a. slices. At the end of each slice, a state record is emitted to store a checkpoint. This column stores the timestamp when the slice started"),
                _airbyte_emitted_at timestamp options(description="Record ingestion time into BigQuery"),
                _airbyte_data string options(description="Record data as json string")
            )
            partition by date(_airbyte_emitted_at)
            options(
                description="{table} records ingested by simple_airbyte"
            )
        '''
        import google.cloud.bigquery
        self.bigquery = google.cloud.bigquery.Client(project=project)
        for table in self.tables.values():
            self.bigquery.query(create_table_query.format(dataset=dataset, table=table)).result()

    def insert_rows(self, table, records):
        if not records:
            return
        table = f'{self.dataset}.{self.tables[table]}'
        now  = datetime.datetime.utcnow().isoformat()
        records = [
            {
                '_airbyte_ab_id': str(uuid.uuid4()),
                '_airbyte_job_started_at': self.job_started_at,
                '_airbyte_slice_started_at': self.slice_started_at,
                '_airbyte_emitted_at': now,
                '_airbyte_data': record,
            }
            for record in records
        ]
        errors = self.bigquery.insert_rows_json(table, records)
        if errors:
            raise ValueError(f'Could not insert rows to BigQuery table {table}. Errors: {errors}')

    def load(self, messages):
        self.job_started_at = datetime.datetime.utcnow().isoformat()
        self.slice_started_at = self.job_started_at
        buffer = []
        stream = None
        for message in messages:
            if message['type'] == 'RECORD':
                new_stream = message['record']['stream']
                if new_stream != stream and stream is not None:
                    self.insert_rows(stream, buffer)
                    buffer = []
                    self.slice_started_at = datetime.datetime.utcnow().isoformat()
                stream = new_stream
                buffer.append(json.dumps(message['record']['data']))
                if len(buffer) > self.buffer_size_max:
                    self.insert_rows(stream, buffer)
                    buffer = []
            elif message['type'] == 'STATE':
                self.insert_rows(stream, buffer)
                buffer = []
                self.insert_rows('airbyte_states', [json.dumps(message['state'])])
                self.slice_started_at = datetime.datetime.utcnow().isoformat()
            elif message['type'] == 'LOG':
                message = json.dumps(message['log'])
                self.insert_rows('airbyte_logs', [message])
            elif message['type'] == 'TRACE':
                message = json.dumps(message['trace'])
                self.insert_rows('airbyte_logs', [message])
            else:
                raise NotImplementedError(f'message type {message["type"]} is not managed yet')
        self.insert_rows(stream, buffer)

    def get_state(self):
        rows = self.bigquery.query(f'''
            select json_extract(data, '$.data') as state
            from {self.tables['airbyte_state']}
            order by _airbyte_emitted_at desc
            limit 1
        ''').result()
        rows = list(rows)
        return json.loads(rows[0].state) if rows else {}
