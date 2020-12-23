#!/bin/bash
export $(cat .env | xargs) &&
gcloud functions deploy eq-submission-confirmation-consumer \
    --entry-point notify --runtime python39 --trigger-http \
    --set-env-vars NOTIFY_TEMPLATE_ID=${NOTIFY_TEMPLATE_ID},NOTIFY_API_KEY=${NOTIFY_API_KEY} \
    --region=europe-west2