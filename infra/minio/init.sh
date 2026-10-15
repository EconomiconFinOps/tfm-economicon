#!/bin/sh
set -eu
umask 077
export MC_CONFIG_DIR=/tmp/mc
mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
mc mb --ignore-existing "local/$DOCUMENT_S3_BUCKET" >/dev/null
mc anonymous set none "local/$DOCUMENT_S3_BUCKET" >/dev/null
mc admin user add local "$DOCUMENT_S3_ACCESS_KEY" "$DOCUMENT_S3_SECRET_KEY" >/dev/null
python - <<'PY'
import json, os
bucket = os.environ['DOCUMENT_S3_BUCKET']
policy = {'Version': '2012-10-17', 'Statement': [
    {'Effect': 'Allow', 'Action': ['s3:ListBucket', 's3:GetBucketLocation'], 'Resource': [f'arn:aws:s3:::{bucket}']},
    {'Effect': 'Allow', 'Action': ['s3:GetObject', 's3:PutObject', 's3:DeleteObject'], 'Resource': [f'arn:aws:s3:::{bucket}/*']},
]}
with open('/tmp/document-policy.json', 'w') as stream:
    json.dump(policy, stream)
PY
mc admin policy create local document-ingestion /tmp/document-policy.json >/dev/null
mc admin policy attach local document-ingestion --user "$DOCUMENT_S3_ACCESS_KEY" >/dev/null
# Expiration is a fallback for STAGING only; confirmed originals have SQL-owned retention.
# This dedicated bucket is owned by this service; importing a fixed ID avoids duplicate rules.
printf '%s' '{"Rules":[{"ID":"document-staging-expiration-v1","Status":"Enabled","Filter":{"Prefix":"staging/"},"Expiration":{"Days":1}}]}' | mc ilm import "local/$DOCUMENT_S3_BUCKET" >/dev/null
