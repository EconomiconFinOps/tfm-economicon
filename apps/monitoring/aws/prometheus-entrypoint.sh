#!/bin/sh
set -eu
printf '%s' "$MONITORING_NAMESPACE" | grep -Eq '^economicon-[a-z0-9-]+\.internal$'
sed "s/__NAMESPACE__/$MONITORING_NAMESPACE/g" /etc/prometheus/template.yml > /prometheus/config.yml
exec /bin/prometheus --config.file=/prometheus/config.yml --storage.tsdb.path=/prometheus/data --storage.tsdb.retention.time=24h --storage.tsdb.retention.size=256MB --web.listen-address=127.0.0.1:9090
