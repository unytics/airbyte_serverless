
![logo](https://github.com/unytics/airbyte_serverless/assets/111615732/c922cc30-9391-4d42-8aff-8b2b4c68bd29)


<p align="center">
    <em>Airbyte made simple</em>
</p>

---

<br>

## 🔍️ What is AirbyteServerless?

AirbyteServerless is a simple tool to **manage Airbyte connectors**, run them **locally** or deploy them in **serverless** mode.

<br>

## 💡  Why AirbyteServerless?

[Airbyte](https://airbyte.com/) is a must-have in your data-stack with its **catalog of open-source connectors to move your data from any source to your data-warehouse**.

To manage these connectors, Airbyte offers **Airbyte-Open-Source-Platform** which includes a server, workers, database, UI, orchestrator, connectors, secret manager, logs manager, etc. 

AirbyteServerless aims at offering **a lightweight alternative** to Airbyte-Open-Source-Platform to simplify connectors management.

<br>

## 📝 Comparing Airbyte-Open-Source-Platform & AirbyteServerless

| Airbyte-Open-Source-Platform    | AirbyteServerless |
| -------- | ------- |
| **Has a UI** | **Has NO UI**<br>Connections configurations are managed by documented yaml files |
| **Has a database**  | **Has NO database**<br>- Configurations files are versioned in git<br>- The destination stores the `state` (the [checkpoint](https://airbyte.com/blog/checkpointing) of where sync stops) and `logs` which can then be visualized with your preferred BI tool |
| **Has a transform layer**<br>Airbyte loads your data in a raw format but then enables you to perform basic transform such as replace, upsert, [schema normalization](https://docs.airbyte.com/understanding-airbyte/basic-normalization/)   | **Has NO transform layer**<br>- Data is appended in your destination in raw format.<br>- `airbyte_serverless` is dedicated to do one thing and do it well: `Extract-Load`. |
| **NOT Serverless**<br>- Can be deployed on a VM or Kubernetes Cluster.<br>- The platform is made of tens of dependent containers that you CANNOT deploy with serverless  | **Serverless**<br>- An Airbyte source docker image is upgraded with a destination connector<br>- The upgraded docker image can then be deployed as an isolated `Cloud Run Job` (or `Cloud Run Service`)<br>- Cloud Run is natively monitored with metrics, dashboards, logs, error reporting, alerting, etc<br>- It can be scheduled or triggered by events  |
| **Is scalable with conditions**<br>Scalable if deployed on autoscaled Kubernetes Cluster and if you are skilled enough.<br>👉 **Check that you are skilled enough with Kubernetes by watching [this video](https://www.youtube.com/watch?v=9wvEwPLcLcA)** 😁. | **Is scalable**<br>Each connector is deployed independently of each other. You can have as many as you want. |

<br> 

## 💥 Getting Started with `abs` CLI

`abs` is the CLI (command-line-interface) of AirbyteServerless which facilitates connectors management.

### Install `abs` 🛠️

``` sh
pip install airbyte-serverless
```

### Create your first Connection 👨‍💻

``` sh
abs create my_first_connection --source="airbyte/source-faker:0.1.4" --destination="bigquery:my_project.my_dataset"
```

> 1. Docker is required. Make sure you have it installed.
> 2. `source` param can be any Public Docker Airbyte Source ([here](https://hub.docker.com/search?q=airbyte%2Fsource-) is the list). We recomend that you use faker source to get started.
> 4. `destination` param must be one of the following:
>     - `print`
>     - `bigquery:my_project.my_dataset` with `my_project` a GCP project where you can run BigQuery queries and `my_dataset` a BigQuery dataset where you have `dataEditor` permission.
>     - *contributions are welcome to offer more destinations* 🤗
> 6. The command will create a configuration file `./connections/my_first_connection.yaml` with initialized configuration.
> 8. Update this configuration file to suit your needs.


### Run it! ⚡

``` sh
abs run my_first_connection
```

> 1. The `run`commmand will only work if you have correctly edited `./connections/my_first_connection.yaml` configuration file.
> 2. If you chose `bigquery` destination, you must have `gcloud` installed on your machine with default credentials initialized with the command `gcloud auth application-default login`
> 4. Data is always appended at destination (not replaced nor upserted). It will be in raw format.
> 5. If the connector supports incremental extract (extract only new or recently modified data) then this mode is chosen.


### Select only some streams 🧛🏼

You may not want to copy all the data that the source can get. To see all available `streams` run:

``` sh
abs list-streams my_first_connection
```

Run extract-load for only `stream1` and `stream2` with:

``` sh
abs run my_first_connection --streams="stream1,stream2"
```

If you want to persist the choice of these streams for all future extract-loads, run:

``` sh
abs set-config my_first_connection --streams="stream1,stream2"
```


### Get help 📙

``` sh
$ abs --help
Usage: abs [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  deploy  Deploy BIGFUNCTION
  doc     Generate, serve and publish documentation
  test    Test BIGFUNCTION
```


### Deploy 🚀

...

<br>

## 👋 Contribute 

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

<br>

## 🏆 Credits

- Big kudos to Airbyte for all the hard work on connectors!
- The generation of the sample connector configuration in yaml is heavily inspired from the code of `octavia` CLI developed by airbyte.
