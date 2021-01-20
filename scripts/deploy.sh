#!/bin/bash
if [[ -z "$NOTIFY_API_KEY" ]]; then
    echo "NOTIFY_API_KEY must be provided" 1>&2
    exit 1
fi
if [[ -z "$NOTIFY_TEST_TEMPLATE" ]]; then
    echo "NOTIFY_TEST_TEMPLATE must be provided" 1>&2
    exit 1
fi
export $(cat .env | xargs) &&
gcloud functions deploy eq-submission-confirmation-consumer \
    --entry-point notify --runtime python39 --trigger-http \
    --set-env-vars NOTIFY_TEST_TEMPLATE_ID=${NOTIFY_TEST_TEMPLATE_ID},NOTIFY_API_KEY=${NOTIFY_API_KEY} \
    --region=europe-west2