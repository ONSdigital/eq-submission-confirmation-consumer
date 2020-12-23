# eq-submission-confirmation-consumer

Google Cloud Function that uses an http listener to respond to Cloud Tasks.

On instantiation the function forwards the request on to Gov Notify, which is responsible for sending the appropriate email.

## Development

Local development uses Pipenv to manage the Python environment. Make sure you have Pipenv installed and are using Python version 3.8.

There are two environment variables required to run the function:

- NOTIFY_TEMPLATE_ID (the id of the email template that will be sent to users).
- NOTIFY_API_KEY (the key used to authenticate with Gov Notify - make sure to use a test key for local dev).

NOTIFY_TEMPLATE_ID is provided via the .development.env file, but you will need to set the NOTIFY_API_KEY yourself as it is not kept in version control.

## Deployment from local machine

For development purposes it is possible to deploy the function to GCP from a local machine using the `gcloud` command. First login using `gcloud auth login`, then set the application default credentials using `gcloud auth application-default login`.

If this is the first time deploying a Cloud Function to a project, the Cloud Build API may need to be enabled - navigate to `https://console.developers.google.com/apis/library/cloudbuild.googleapis.com?project=your-project-name` to enable it

Once authenticated, run `make deploy`.
