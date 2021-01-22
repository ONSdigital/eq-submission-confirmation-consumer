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

Once authenticated, run `NOTIFY_API_KEY=<your-api-key> make deploy`.
