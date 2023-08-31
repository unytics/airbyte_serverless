import os
import json
import inspect
import datetime
import uuid

import airbyte_cdk

from .utils import print_info



def create_file_or_try_to_open(filename):
    try:
        open(filename, 'a').close()
    except:
        raise ValueError(f'Cannot create or open file {filename}')


def get_latest_line_of_file(filename):
    with open(filename, 'rb') as f:
        try:  # catch OSError in case of a one line file
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        return f.readline().decode(encoding='utf-8')


class BaseDestination:

    def __init__(self, catalog):
        self.catalog = catalog
        self.streams = [s['stream']['name'] for s in catalog['streams']]

    def get_state(self):
        raise NotImplementedError()

    def get_logs(self):
        raise NotImplementedError()

    def run(self, messages):
        raise NotImplementedError()

    @classmethod
    def get_class_name(cls):
        return cls.__name__.lower().replace('destination', '')

    @classmethod
    def get_init_help(cls):
        argspec = inspect.getfullargspec(cls.__init__)
        if argspec.defaults:
            args = argspec.args[:-len(argspec.defaults)]
        else:
            args = argspec.args
        args = ', '.join([arg.upper() for arg in args if arg not in ['self', 'catalog']])
        return f'{cls.get_class_name()}({args})'


class PrintDestination(BaseDestination):

    def run(self, messages):
        for message in messages:
            print(message.json(exclude_unset=True))


class LocalJsonDestination(BaseDestination):

    def __init__(self, catalog, folder):
        super().__init__(catalog)
        os.makedirs(folder, exist_ok=True)
        self.states_file = f'{folder}/states.jsonl'
        self.logs_file = f'{folder}/logs.jsonl'
        self.stream_file = lambda stream: f'{folder}/{stream}.jsonl'
        create_file_or_try_to_open(self.states_file)
        create_file_or_try_to_open(self.logs_file)
        for stream in self.streams:
            create_file_or_try_to_open(self.stream_file(stream))

    def get_state(self):
        content = get_latest_line_of_file(self.states_file)
        if not content:
            return {}
        else:
            state = json.loads(content)
            return state['data']

    def run(self, messages):
        states_file = open(self.states_file, 'a', encoding='utf-8')
        logs_file = open(self.logs_file, 'a', encoding='utf-8')
        streams_files = {
            stream: open(self.stream_file(stream), 'a', encoding='utf-8')
            for stream in self.streams
        }
        try:
            for message in messages:
                if message.type == airbyte_cdk.models.Type.LOG:
                    message = message.log.json(exclude_unset=True)
                    print_info(message)
                    logs_file.write(message + '\n')
                elif message.type == airbyte_cdk.models.Type.RECORD:
                    file = streams_files[message.record.stream]
                    row = json.dumps(message.record.data)
                    file.write(row + '\n')
                elif message.type == airbyte_cdk.models.Type.STATE:
                    states_file.write(message.state.json(exclude_unset=True) + '\n')
        finally:
            states_file.close()
            logs_file.close()
            for stream_file in streams_files.values():
                stream_file.close()


class BigQueryDestination(BaseDestination):

    def __init__(self, catalog, dataset, buffer_size_max=10000):
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
                description="{table} records ingested by bigloader"
            )
        '''
        import google.cloud.bigquery
        self.bigquery = google.cloud.bigquery.Client()
        for table in self.tables.values():
            self.bigquery.query(create_table_query.format(dataset=dataset, table=table)).result()

    def insert_rows(self, table, records):
        if not records:
            return
        table = f'{self.dataset}.{table}'
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

    def run(self, messages):
        self.job_started_at = datetime.datetime.utcnow().isoformat()
        self.slice_started_at = self.job_started_at
        buffer = []
        stream_table = None
        for message in messages:
            if message.type == airbyte_cdk.models.Type.RECORD:
                new_stream_table = self.tables[message.record.stream]
                if new_stream_table != stream_table and stream_table is not None:
                    self.insert_rows(stream_table, buffer)
                    buffer = []
                    self.slice_started_at = datetime.datetime.utcnow().isoformat()
                stream_table = new_stream_table
                buffer.append(json.dumps(message.record.data))
                if len(buffer) > self.buffer_size_max:
                    self.insert_rows(stream_table, buffer)
                    buffer = []
            elif message.type == airbyte_cdk.models.Type.STATE:
                self.insert_rows(stream_table, buffer)
                buffer = []
                self.insert_rows(self.tables['airbyte_states'], [message.state.json(exclude_unset=True)])
                self.slice_started_at = datetime.datetime.utcnow().isoformat()
            elif message.type == airbyte_cdk.models.Type.LOG:
                message = message.log.json(exclude_unset=True)
                print_info(message)
                self.insert_rows(self.tables['airbyte_logs'], [message])
            else:
                raise NotImplementedError(f'message type {message.type} is not managed yet')
        self.insert_rows(stream_table, buffer)

    def get_state(self):
        rows = self.bigquery.query(f'''
            select json_extract(data, '$.data') as state
            from {self.tables['airbyte_state']}
            order by _airbyte_emitted_at desc
            limit 1
        ''').result()
        rows = list(rows)
        return json.loads(rows[0].state) if rows else {}



DESTINATIONS = {
    destination.get_class_name(): destination
    for destination in [LocalJsonDestination, BigQueryDestination, PrintDestination]
}


def create_destination(destination_arg, catalog):
    destination, args = destination_arg.split('(')
    args = args.replace(')', '').split(',')
    args = [arg.strip() for arg in args if arg.strip()]
    Destination = DESTINATIONS[destination]
    return Destination(catalog, *args)
