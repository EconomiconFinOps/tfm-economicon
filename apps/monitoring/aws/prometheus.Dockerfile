FROM prom/prometheus:v2.55.1@sha256:2659f4c2ebb718e7695cb9b25ffa7d6be64db013daba13e05c875451cf51b0d3
COPY apps/monitoring/aws/prometheus.yml /etc/prometheus/template.yml
COPY apps/monitoring/aws/prometheus-entrypoint.sh /entrypoint-economicon.sh
USER root
RUN chmod 0555 /entrypoint-economicon.sh
USER nobody
VOLUME ["/prometheus"]
ENTRYPOINT ["/entrypoint-economicon.sh"]
