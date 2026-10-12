from sqlalchemy import text


def upgrade(connection) -> None:
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS anomaly_episodes (
                id STRING PRIMARY KEY,
                tenant_id STRING NOT NULL,
                currency STRING NOT NULL,
                service STRING,
                service_key STRING NOT NULL,
                start_date DATE NOT NULL,
                last_seen_date DATE NOT NULL,
                observation STRING NOT NULL CHECK (observation IN ('observed', 'no_longer_observed')),
                no_longer_observed_on DATE,
                reference_week_cost DECIMAL NOT NULL,
                opening_observed_cost DECIMAL NOT NULL,
                impact_numerator DECIMAL NOT NULL,
                impact_day_count INT NOT NULL,
                impact_through_date DATE NOT NULL,
                severity STRING NOT NULL CHECK (severity IN ('P1', 'P2', 'P3')),
                status STRING NOT NULL CHECK (status IN ('new', 'investigating', 'resolved', 'false_positive')),
                status_changed_by STRING,
                status_changed_at TIMESTAMPTZ,
                first_reviewed_at TIMESTAMPTZ,
                closed_at TIMESTAMPTZ,
                closure_reason STRING,
                previous_episode_id STRING,
                rules_version STRING NOT NULL,
                rules JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    )
    # A double press or a concurrent run cannot leave two episodes tracking one group.
    connection.execute(
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS anomaly_episodes_one_tracking
            ON anomaly_episodes (tenant_id, currency, service_key)
            WHERE observation = 'observed' AND status IN ('new', 'investigating')
            """
        )
    )
    connection.execute(
        text("CREATE INDEX IF NOT EXISTS anomaly_episodes_tenant_start ON anomaly_episodes (tenant_id, start_date)")
    )
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS anomaly_detection_state (
                tenant_id STRING PRIMARY KEY,
                last_evaluated_date DATE NOT NULL,
                rules_version STRING NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    )
