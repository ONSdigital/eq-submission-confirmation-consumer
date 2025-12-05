#!/bin/bash
gcloud functions deploy eq-submission-confirmation-consumer \
    --entry-point send_email --runtime python313 --trigger-http \
    --region=europe-west2 -q
