#!/bin/bash
export $(cat .env | xargs) &&
if [[ -z "$NOTIFY_API_KEY" ]]; then
    echo "NOTIFY_API_KEY must be provided" 1>&2
    exit 1
fi
if [[ -z "$NOTIFY_TEST_TEMPLATE_ID" ]]; then
    echo "NOTIFY_TEST_TEMPLATE must be provided" 1>&2
    exit 1
fi
gcloud functions deploy eq-submission-confirmation-consumer \
    --entry-point send_email --runtime python39 --trigger-http \
    --set-env-vars NOTIFY_TEST_TEMPLATE_ID=${NOTIFY_TEST_TEMPLATE_ID},NOTIFY_API_KEY=${NOTIFY_API_KEY} \
    --region=europe-west2
