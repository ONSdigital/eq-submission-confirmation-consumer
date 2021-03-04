# eq-submission-confirmation-consumer

Google Cloud Function that uses an HTTP listener to respond to HTTP requests.

On instantiation the function forwards the request on to Gov Notify, which is responsible for sending the appropriate email.

## Development

Local development uses Pipenv to manage the Python environment. Make sure you have Pipenv installed and are using Python version 3.8.

There are two environment variables required to run the function:

- NOTIFY_API_KEY (the key used to authenticate with Gov Notify - make sure to use a test key for local dev).

The TCP port defaults to port `8080` but can be overriden by setting the `PORT` env var.

## Testing

To run the tests, make sure you have set `NOTIFY_API_KEY` to the Notify test key, and run `make test`. This will spin up a local functions-framework process against which the integration tests are run.

If you wish to carry out manual testing, be sure to use the email address `simulate-delivered@notifications.service.gov.uk` in the payload, as this does not trigger any actions on the Notify project (https://docs.notifications.service.gov.uk/rest-api.html#smoke-testing).

## Deployment from local machine

For development purposes it is possible to deploy the function to GCP from a local machine using the `gcloud` command. First login using `gcloud auth login`, then set the application default credentials using `gcloud auth application-default login`. Be sure to make the current gcloud project id the one you wish to deploy to `gcloud config set project <your-project-id>`

If this is the first time deploying a Cloud Function to a project, the Cloud Build and Cloud Functions APIs may need to be enabled - navigate to `https://console.developers.google.com/apis/library/cloudbuild.googleapis.com?project=your-project-name` and `https://console.developers.google.com/apis/library/cloudfunctions.googleapis.com?project=your-project-name` to enable them.

For the cloud function to work it needs a valid Notify API key, this can be provided in two ways - a `notify_api_key` secret in GCP Secret Manager or a `NOTIFY_API_KEY` environment variable. The environment variable should only be used for development or testing, it should never be used for a formal environment.

**Secret Manager in GCP**

Firstly check that Secret Manager in GCP is enabled, if not enable it. You can add the `notify_api_key` manually in the UI or use the gcloud commands below. If doing it manually, go to Secret Manager in GCP and click `Create Secret`, enter the name as `notify_api_key` and your secret value, a region can also be set if required.

Once the secret has been created, click on the name `notify_api_key` and expand the info panel on the right if not already showing. In this menu click add member and fill out the form, member should be `<project_id>@appspot.gserviceaccount.com` and role should be `Secret Manager Secret Accessor`

If using gcloud commands run the following

```
gcloud secrets create notify_api_key --data-file=<data_file> --project=<project_id> --replication-policy=<replication-policy> --locations=<locations>

gcloud secrets add-iam-policy-binding `notify_api_key` --role roles/secretmanager.secretAccessor --member serviceAccount:<project_id>@appspot.gserviceaccount.com
```

N.B. replication-policy can be `automatic` or `user-managed`. If automatic neither `replication-policy` or `location` needs to be included in the command, if user-managed `replication-policy` and `location` must be provided

**Deploying with an environment variable**

You can also use an environment variable if you do not have access to Secret Manager, you can do this by updating the `deploy_function.sh` to include `--set-env-vars NOTIFY_API_KEY=<notify_api_key>`


Once authenticated and the notify_api_key set, run `make deploy_function`.


## Deleting from local machine

For development purposes it is possible to delete the function in GCP from a local machine using the `gcloud` command. First login using `gcloud auth login`, then set the application default credentials using `gcloud auth application-default login`. Be sure to make the current gcloud project id the one you wish to deploy to `gcloud config set project <your-project-id>`

Once authenticated, run `make delete_function`.
