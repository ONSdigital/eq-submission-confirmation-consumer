#!/usr/bin/env bash
set -euxo pipefail

if [[ -z "$PROJECT_ID" ]]; then
  echo "PROJECT_ID not provided"
  exit 1
fi

if [[ -z "$NOTIFY_API_KEY_FILE" ]]; then
  echo "NOTIFY_API_KEY_FILE not provided"
  exit 1
fi

KEY_NAME="notify_api_key"
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")

gcloud secrets create "$KEY_NAME" --replication-policy="automatic" --project="$PROJECT_ID" || true
gcloud secrets versions add "$KEY_NAME" --data-file="$NOTIFY_API_KEY_FILE" --project="$PROJECT_ID"

# Give the default compute service account access to this secret
gcloud secrets add-iam-policy-binding "$KEY_NAME" --role roles/secretmanager.secretAccessor \
  --member "serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" --project="$PROJECT_ID"