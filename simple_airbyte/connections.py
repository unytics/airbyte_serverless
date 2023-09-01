from .sources import AirbyteSource
from .destinations import BigQueryDestination


class AirbyteSource2Destination:

    def __init__(
            self,
            airbyte_source_executable,
            airbyte_source_config=None,
            airbyte_configured_catalog=None,
            **destination_config
        ):
        self.airbyte_source = AirbyteSource(
            airbyte_source_executable,
            config=airbyte_source_config,
            configured_catalog=airbyte_configured_catalog
        )
        self._destination = None
        self.destination_config = destination_config

    @property
    def destination(self):
        raise NotImplementedError()

    def run(self, command):
        if command != 'read':
            return getattr(self.airbyte_source, command)

        state = self.destination.get_state()
        messages = self.airbyte_source.read(state=state)
        self.destination.load(messages)
        return {'status': 'success'}


class AirbyteSource2BigQuery(AirbyteSource2Destination):

    @property
    def destination(self):
        if self._destination is None:
            self._destination = BigQueryDestination(
                self.airbyte_source.configured_catalog,
                **self.destination_config
            )
        return self._destination
