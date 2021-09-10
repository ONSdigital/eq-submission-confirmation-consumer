## Pause Cloud Task queue

A cloud task queue can be paused by using the `pause_cloud_task_queue.yaml` task. This can be done via Concourse using the following command:

```sh
PROJECT_ID=<project_id> \
QUEUE_NAME=<queue_name> \
fly -t <target-concourse> execute \
  --config ci/pause_cloud_task_queue.yaml
```

## Resume Cloud Task queue

A cloud task queue can be resumed by using the `resume_cloud_task_queue.yaml` task. This can be done via Concourse using the following command:

```sh
PROJECT_ID=<project_id> \
QUEUE_NAME=<queue_name> \
fly -t <target-concourse> execute \
  --config ci/resume_cloud_task_queue.yaml
```

## Deploy Credentials

The `notify_api_key` can be provisioned into GCP Secret Manager using the `deploy_credentials.yaml` task. This can be done via Concourse using the following command:

```sh
PROJECT_ID=<project_id> \
NOTIFY_API_KEY_FILE=<notify_api_key_file> \
fly -t <target-concourse> execute \
  --config ci/deploy_credentials.yaml
```

## Destroy Credentials

The `notify_api_key` can be deleted from GCP Secret Manager using the `destroy_credentials.yaml` task. This can be done via Concourse using the following command:

```sh
PROJECT_ID=<project_id> \
fly -t <target-concourse> execute \
  --config ci/destroy_credentials.yaml
```
