
![logo](https://github.com/unytics/airbyte_serverless/assets/111615732/c922cc30-9391-4d42-8aff-8b2b4c68bd29)


<p align="center">
    <em>Airbyte made simple</em>
</p>

---

<br>

## 🔍️ What is AirbyteServerless?

AirbyteServerless is a simple tool to **manage Airbyte connectors**, run them **locally** or deploy them in **serverless** mode.

![logo](https://raw.githubusercontent.com/unytics/airbyte_serverless/main/airbyte_serverless.gif)



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

### Create your first Connection with a Docker Source from DockerHub 👨‍💻

``` sh
abs create my_first_connection --source="airbyte/source-faker:0.1.4" --destination="bigquery" --remote-runner "cloud_run_job"
```

> 1. Docker is required. Make sure you have it installed. (IF YOU DON'T HAVE DOCKER AND WANT TO RUN A PYTHON CONNECTOR, READ NEXT SECTION)
> 2. `source` param can be any Public Docker Airbyte Source ([here](https://hub.docker.com/search?q=airbyte%2Fsource-) is the list). We recomend that you use faker source to get started.
> 3. `destination` param must be one of the following:
>     - `print` (default value if not set)
>     - `bigquery`
>     - *contributions are welcome to offer more destinations* 🤗
> 4. `remote-runner` param must be `cloud_run_job`. More integrations will come in the future. This remote-runner is only used if you want to run the connection on a remote runner and schedule it.
> 5. The command will create a configuration file `./connections/my_first_connection.yaml` with initialized configuration.
> 6. Update this configuration file to suit your needs.


### Create your first Connection with a Python Source from PyPI 👨‍💻

Actually, `source` argument can be a docker image as above or any command.

Below, we use `pipx` tool to run [`airbyte-source-faker` python package available on pypi](https://pypi.org/project/airbyte-source-faker/).

``` sh
abs create my_first_connection --source="pipx run airbyte-source-faker==0.1.4"
```

The value just after `pipx run` can be any Airbyte Python Source [available on pypi](https://pypi.org/search/?q=airbyte-source-). For security reasons, beware to check that the source you are going to install is really from Airbyte.

The other arguments are the same as before.


### Run it! ⚡

``` sh
abs run my_first_connection
```

> 1. This will launch an Extract-Load Job from the source to the destination.
> 2. The `run` commmand will only work if you have correctly edited `./connections/my_first_connection.yaml` configuration file.
> 3. If you chose `bigquery` destination, you must:
>    + have `gcloud` installed on your machine with default credentials initialized with the command `gcloud auth application-default login`.
>    + have correctly edited the `destination` section of `./connections/my_first_connection.yaml` configuration file. You must have `dataEditor` permission on the chosen BigQuery dataset.
> 4. Data is always appended at destination (not replaced nor upserted). It will be in raw format.
> 5. If the connector supports incremental extract (extract only new or recently modified data) then this mode is chosen.


### Select only some streams 🧛🏼

You may not want to copy all the data that the source can get. To see all available `streams` run:

``` sh
abs list-available-streams my_first_connection
```

If you want to configure your connection with only some of these streams, run:

``` sh
abs set-streams my_first_connection "stream1,stream2"
```

Next `run` executions will extract selected streams only.


### Handle Secrets 🔒

For security reasons, you do NOT want to store secrets such as api tokens in your yaml files. Instead, add your secrets in Google Secret Manager by following [this documentation](https://cloud.google.com/secret-manager/docs/create-secret-quickstart). Then you can add the secret resource name in the yaml file such as below:

```yaml
source:
  docker_image: "..."
  config:
    api_token: GCP_SECRET({SECRET_RESOURCE_NAME})
```

Replace `{SECRET_RESOURCE_NAME}` by your secret resource name which must have the format: `projects/{PROJECT_ID}/secrets/{SECRET_ID}/versions/{SECRET_VERSION}`. To get this path:

> 1. Go to the [Secret Manager page](https://console.cloud.google.com/security/secret-manager) in the Google Cloud console.
> 2. Go to the Secret Manager page
> 3. On the Secret Manager page, click on the Name of a secret.
> 4. On the Secret details page, in the Versions table, locate a secret version to access.
> 5. In the Actions column, click on the three dots.
> 6. Click on 'Copy Resource Name' from the menu.



### Run from the Remote Runner 🚀

WARNING: THIS ONLY WORKS FOR NOW WITH A DOCKER SOURCE in python language.

``` sh
abs remote-run my_first_connection
```
> 2. The `remote-run` commmand will only work if you have correctly edited `./connections/my_first_connection.yaml` configuration file including the `remote_runner` part.

> 1. This command will launch an Extract-Load Job like the `abs run` command. The main difference is that the command will be run on a remote deployed container (we use Cloud Run Job as the only container runner for now).
> 3. If you chose `bigquery` destination, the service account you put in `service_account` field of `remote_runner` section of the yaml must be `bigquery.dataEditor` on the target dataset and have permission to create some BigQuery jobs in the project.
> 4. If your yaml config contains some Google Secrets, the service account you put in `service_account` field of `remote_runner` section of the yaml must have read access to the secrets.


### Use your own Airbyte Source 🔨

When you create a connection using `abs create my_connection --source "SOURCE"`, you can put any docker image you have access to as `SOURCE`. So `SOURCE` can be:

- a public docker image from Docker Hub
- a local docker image that you built
- a docker image that you built and pushed on [Google Artifact Registry](https://cloud.google.com/artifact-registry/docs/docker).

To run remotely on a cloud run job, the image must be available to Cloud Run (so cannot be local). It must be either public from Docker Hub or from Google Artifact Registry.


### Schedule the run from the Remote Runner ⏱️

``` sh
abs schedule-remote-run my_first_connection "0 * * * *"
```

> ⚠️ THIS IS NOT IMPLEMENTED YET



### Get help 📙

``` sh
$ abs --help
Usage: abs [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  create                  Create CONNECTION
  list                    List created connections
  list-available-streams  List available streams of CONNECTION
  remote-run              Run CONNECTION Extract-Load Job from remote runner
  run                     Run CONNECTION Extract-Load Job
  run-env-vars            Run Extract-Load Job configured by environment...
  set-streams             Set STREAMS to retrieve for CONNECTION (STREAMS...
```

<br>




## ❓ FAQ

<details>
  <summary><b>Is it easy to migrate from/to Airbyte?</b></summary>
  <br>

  1. AirbyteServerless uses Airbyte source connectors. Then, the same config is used. If it works on AirbyteServerless, it will work on Airbyte. The reverse may be sometimes a bit harder if for some sources you created credentials using oauth2 (with a pop-up window from the source opened by Airbyte UI). Indeed, Airbyte may not give you a way to read these created credentials.
  2. Airbyte jobs have two steps: extract-load of raw data and optional transform (transform can be replace, upsert, basic normalization). The extract-load of raw data is exactly the same but AirbyteServerless does not do transform. It only appends raw data at the destination. This is for purpose as AirbyteServerless was made to do only one thing and do it well and we believe it makes it resilient to schema changes. Then,
      - if you create your transforms from raw data on dbt, you will be able to migrate from AirbyteServerless to Airbyte and vice-versa and still use your transforms.
      - if you use Airbyte and rely on Airbyte transforms, you will need to re-create them in dbt if you switch to AirbyteServerless
  3. When migrating from/to Airbyte Cloud ↔ Airbyte OSS self-deployed ↔ AirbyteServerless, you won't be able to copy the state (which stores where incremental jobs stop). Then you will need to make a full refresh.

  <br>
</details>

<details>
  <summary><b>Why cannot we use usual Airbyte destination connectors?</b></summary>
  <br>

  Airbyte-Serverless destination connectors are indeed specific to AirbyteServerless and can NOT be the ones from Airbyte. This is because, in AirbyteServerless, destination connectors manage the states and logs while in Airbyte this is handled by the platform. Thanks to this, we don't need a database 🥳!

  This being said, AirbyteServerless destination connectors are very light. You'll find [here](https://github.com/unytics/airbyte_serverless/blob/main/airbyte_serverless/destinations.py#L105) that the BigQuery destination connector is only 50 lines of code.

  <br>
</details>


<br>


## Keep in touch 🧑‍💻

[Join our Slack](https://join.slack.com/t/unytics/shared_invite/zt-1gbv491mu-cs03EJbQ1fsHdQMcFN7E1Q) for any question, to get help for getting started, to speak about a bug, to suggest improvements, or simply if you want to have a chat 🙂.

<br>

## 👋 Contribute

Any contribution is more than welcome 🤗!
- Add a ⭐ on the repo to show your support
- [Join our Slack](https://join.slack.com/t/unytics/shared_invite/zt-1gbv491mu-cs03EJbQ1fsHdQMcFN7E1Q) and talk with us
- Raise an issue to raise a bug or suggest improvements
- Open a PR! Below are some suggestions of work to be done:
  - implements a scheduler
  - create a very light python Airbyte source / add a tutorial to use it in abs
  - implement the `get_logs` method of `BigQueryDestination`
  - use the new BigQuery Storage Write API for bigquery destination
  - enable updating cloud run job instead of deleting/creating when it already exists
  - add a new destination connector (Cloud Storage?)
  - add more remote runners such compute instances.
  - implements vpc access
  - implement optional post-processing (replace, upsert data at destination instead of append?)

<br>

## 🔨 Credits

- Big kudos to Airbyte for all the hard work on connectors!
- The generation of the sample connector configuration in yaml is heavily inspired from the code of `octavia` CLI developed by Airbyte.
