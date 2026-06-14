from sqlalchemy import text


def upgrade(connection) -> None:
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id STRING PRIMARY KEY,
                tenant_id STRING NOT NULL,
                created_by STRING NOT NULL,
                source STRING NOT NULL,
                artifact_uri STRING,
                payload JSONB NOT NULL,
                status STRING NOT NULL,
                result JSONB,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    )
