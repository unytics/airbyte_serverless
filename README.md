
![logo](https://raw.githubusercontent.com/unytics/simple_airbyte/main/logo.png)

<p align="center">
    <em>Airbyte made simple</em>
</p>

---

## Why `simple_airbyte` ?

At [Unytics](https://www.linkedin.com/company/unytics/), we ❤️ [Airbyte](https://airbyte.com/) which provides a catalog of open-source connectors to move your data from any source to your data-warehouse.

Airbyte provides a very nice UI for configuring and orchestrating connectors. However, it comes with a lot of parts to understand and manage: a server, a database, an orchestrator, a frontend, etc.

> **👉 We wanted a simple tool to manage Airbyte connectors, run them locally or deploy them in *serverless* mode.**


## Features

`simple_airbyte` offers:

> 1. A lightweight python wrapper around any Airbyte Source executable. It comes with:
>     - sample `config` generation in yaml to ease configuration.
>     - sample `configured_catalog` generation
> 2. Destination Connectors (only BigQuery for now - *contibutions are welcome* 🤗) which store `logs` and `states` in addition to data. Thus, there is **no need for a database any more!**
> 3. Examples to deploy to **serverless** compute (only Google Cloud Run for now - *contibutions are welcome* 🤗)


## Install

```bash
pip install simple-airbyte
```


## Usage

### Move data from `SurveyMonkey` to BigQuery `destination_dataset`

```python
from simple_airbyte.connections import AirbyteSource2BigQuery

airbyte_source_executable = 'docker run --rm -i airbyte/source-surveymonkey:latest'
connection = AirbyteSource2BigQuery(
    airbyte_source_executable,
    config,
    configured_catalog,
    dataset=destination_dataset,
)
connection.run('read')
```


### Generate sample `config` for `SurveyMonkey`

To run the command above, you will need to provide a `config` for SurveyMonkey connector. To do so, the easiest is to generate a `sample_config` and adapt it to match your connection.

```python
from simple_airbyte.sources import AirbyteSource

airbyte_source_executable = 'docker run --rm -i airbyte/source-surveymonkey:latest'
source = AirbyteSource(airbyte_source_executable)
sample_config = source.sample_config
```

### [OPTIONAL] Generate sample `configured_catalog` to choose which data to move

In the above example, if you set `configured_catalog` to `None`, the connector will try to move all the data it can to your destination. You may want to define which `stream` you want to sync. To do so, the easiest is to generate a sample `configured_catalog`

```python
from simple_airbyte.sources import AirbyteSource

airbyte_source_executable = 'docker run --rm -i airbyte/source-surveymonkey:latest'
source = AirbyteSource(airbyte_source_executable, config)
sample_configured_catalog = source.sample_configured_catalog
```


## Limitations

- BigQuery Destination connector only works in append mode
- Data at destination is in raw format. No data parsing is done.

We believe, [like Airbyte](https://docs.airbyte.com/understanding-airbyte/basic-normalization), that it is a good thing to decouple data moving and data transformation. To shape your data you may want to use a tool such as dbt. Thus, we follow the EL-T philosophy.
