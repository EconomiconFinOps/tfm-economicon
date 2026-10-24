FROM grafana/grafana:11.3.0@sha256:a0f881232a6fb71a0554a47d0fe2203b6888fe77f4cefb7ea62bed7eb54e13c3
USER root
COPY apps/backend/app/resources/rds-eu-west-1.pem /etc/grafana/rds-ca.pem
COPY apps/monitoring/grafana/dashboards /opt/economicon/dashboards
COPY apps/monitoring/grafana/provisioning/alerting /etc/grafana/provisioning/alerting
COPY apps/monitoring/aws/provisioning /etc/grafana/provisioning
COPY apps/monitoring/aws/grafana-entrypoint.sh /entrypoint-economicon.sh
RUN chmod 0555 /entrypoint-economicon.sh && mkdir -p /tmp/grafana && chown -R 472:0 /tmp/grafana
ENV GF_PATHS_DATA=/tmp/grafana GF_PATHS_LOGS=/tmp/grafana/logs GF_PATHS_PLUGINS=/tmp/grafana/plugins
VOLUME ["/tmp"]
USER 472
ENTRYPOINT ["/entrypoint-economicon.sh"]
