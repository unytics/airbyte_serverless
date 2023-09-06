
![logo](https://github.com/unytics/airbyte_serverless/assets/111615732/c922cc30-9391-4d42-8aff-8b2b4c68bd29)


<p align="center">
    <em>Airbyte made simple</em>
</p>

---

## Why `airbyte_serverless` ?

> At [Unytics](https://www.linkedin.com/company/unytics/), we ❤️ [Airbyte](https://airbyte.com/) which provides a **catalog of open-source connectors to move your data from any source to your data-warehouse.**

When you want to deploy Airbyte open-source yourself it comes with batteries included: you'll get a server, workers, database, UI, orchestrator, connectors, secret manager, logs manager, etc. All of this is very well packaged and deployable on Kubernetes.

While we believe this is great for most people we strive for lightweight and simple assets to deploy and maintain. What's more, we ❤️ `serverless` to rely on fully managed services 😁.


Questions that may arise when deploying airbyte open-source yourself include:

- How do you manage Authentication if I have a UI?
- How do my connectors scale?
- What do I need to monitor? How?
- How can we backup and restore the database in case of outages?

While the documentation of Airbyte is great and complete, that still represents a lot of questions.


> **👉 We wanted a simple tool to manage Airbyte connectors, run them locally or deploy them in *serverless* mode.**


That's why `airbyte_serverless` is *LESS* than `airbyte`.



## How `airbyte_serverless` is *LESS* than `airbyte` ?

### 1. `airbyte` comes with a database | `airbyte_serverless` does NOT.

Airbyte database stores connectors configuration and the `state` (the track of where the latest sync ended)

Instead
- We rely on the destination to store and manage the `state`
- Connectors configuration can be managed as configuration files that you put on git.


### 2. `airbyte` comes with a UI | `airbyte_serverless` does NOT.

In Airbyte connectors configuration is very easy to set up with a clean UI.

Instead, connectors configuration is initiated with generated documented-yaml-files that you can update and version in git. *(We rely on airbyte source code of their CLI octavia to generate these yaml)*


### 3. `airbyte` comes with workers  | `airbyte_serverless` does NOT.

Airbyte open-source can be deployed on a VM or on Kubernetes. Workers are containers



2. `airbyte` comes with a UI | `airbyte_serverless` does NOT. <br>

> 1. ⚡ A lightweight python wrapper around any Airbyte Source executable. It comes with:
>     - sample `config` generation in yaml to ease configuration.
>     - sample `configured_catalog` generation
> 2. ⚡ Destination Connectors (only BigQuery for now - *contibutions are welcome* 🤗) which store `logs` and `states` in addition to data. Thus, there is **no need for a database any more!**
> 3. ⚡ Examples to deploy to **serverless** compute (only Google Cloud Run for now - *contibutions are welcome* 🤗)


## Install

```bash
pip install simple-airbyte
```


## Getting Started

### 1. Create an Airbyte Source from an Airbyte Source Executable

If you have docker installed on your laptop, the easiest is to write the following code in a file `getting_started.py` (change `surveymonkey` with the source you want). Then, it should directly work when you run `python getting_started.py`. *If it does not, please raise an issue.*


```python
from airbyte_serverless.sources import AirbyteSource

airbyte_source_executable = 'docker run --rm -i airbyte/source-surveymonkey:latest'
source = AirbyteSource(airbyte_source_executable)
```

<details>
  <summary><u>If you don't have docker <i>(or don't want to use it)</i></u></summary>

>  It is also possible to clone airbyte repo and install a python source connector:
>
>  1. Clone the repo
>  2. Go to the directory of the connector: `cd airbyte-integrations/connectors/source-surveymonkey`
>  3. Install the python connector `pip install -r requirements.txt`
>  4. Create here the file `getting_started.py` and set `airbyte_source_executable = 'python main.py'`
>  5. You can now run `python getting_started.py` it then should also work. *If it does not, please raise an issue.*
</details>


### 2. Update `config` for your Airbyte Source

Your Airbyte Source needs some config to be able to connect. Show a pre-filled `config` for your connector with:

```python
print(source.config)
```

Copy the content, edit it and update the variable:

```python
source.config = '''
YOUR UPDATED CONFIG
'''
```


### 3. Check your `config`

```python
print(source.connection_status)
```


### 4. Update `configured_catalog` for your Airbyte Source

The source `catalog` lists the available `streams` (think entities) that the source is able to retrieve. The `configured_catalog` specifies which `streams` to extract and how. Show the default `configured_catalog` with:

```python
print(source.configured_catalog)
```

If needed, copy the content, edit it and update the variable:

```python
source.configured_catalog = {
   ...YOUR UPDATED CONFIG
}
```


### 6. Test the retrieval of one data record

```python
print(source.first_record)
```

### 7. Create a destination and run Extract-Load

To stream `data` from `source` to `destination` run:

```python
from airbyte_serverless.destinations import BigQueryDestination

destination = BigQueryDestination(dataset='YOUR-PROJECT.YOUR_DATASET')
data = source.extract()
destination.load(data)
```


### 8. Run Extract-Load from where you stopped

The `state` keeps track from where the latest extract-load ended (for incremental extract-load).
To start from this `state` run:

```python
state = destination.get_state()
data = source.extract(state=state)
destination.load(data)
```


## End to End Example

```python

from airbyte_serverless.sources import AirbyteSource
from airbyte_serverless.destinations import BigQueryDestination

airbyte_source_executable = 'docker run --rm -i airbyte/source-surveymonkey:latest'
config = 'YOUR CONFIG'
configured_catalog = {YOUR CONFIGURED CATALOG}
source = AirbyteSource(airbyte_source_executable, config=config, configured_catalog=configured_catalog)

destination = BigQueryDestination(dataset='YOUR-PROJECT.YOUR_DATASET')

state = destination.get_state()
data = source.extract(state=state)
destination.load(data)
```




## Deploy

To deploy to Cloud Run job, edit Dockerfile to pick the Airbyte source you like then run:



## Limitations

- BigQuery Destination connector only works in append mode
- Data at destination is in raw format. No data parsing is done.

We believe, [like Airbyte](https://docs.airbyte.com/understanding-airbyte/basic-normalization), that it is a good thing to decouple data moving and data transformation. To shape your data you may want to use a tool such as dbt. Thus, we follow the EL-T philosophy.


## Credits

The generation of the sample connector configuration in yaml is heavily inspired from the code of `octavia` CLI developed by airbyte.


## Contribute

Any contribution is more than welcome 🤗!
- Add a ⭐ on the repo to show your support
- Raise an issue to raise a bug or suggest improvements
- Open a PR! Below are some suggestions of work to be done:
  - improve secrets management
  - implement a CLI
  - manage configurations as yaml files
  - implement the `get_logs` method of `BigQueryDestination`
  - add a new destination connector (Cloud Storage?)
  - add more serverless deployment examples.
  - implement optional post-processing (replace, upsert data at destination instead of append?)
