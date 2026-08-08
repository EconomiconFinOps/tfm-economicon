from sqlalchemy import text


def upgrade(connection) -> None:
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS azure_cost_ingestion_runs (
                id STRING PRIMARY KEY,
                tenant_id STRING NOT NULL,
                subscription_id STRING NOT NULL,
                request JSONB NOT NULL,
                status STRING NOT NULL,
                page_count INT8 NOT NULL DEFAULT 0,
                retry_count INT8 NOT NULL DEFAULT 0,
                row_count INT8 NOT NULL DEFAULT 0,
                error_code STRING,
                started_at TIMESTAMPTZ NOT NULL,
                completed_at TIMESTAMPTZ
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_azure_cost_runs_tenant
            ON azure_cost_ingestion_runs (tenant_id, started_at)
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS azure_cost_records (
                id STRING PRIMARY KEY,
                ingestion_id STRING NOT NULL,
                tenant_id STRING NOT NULL,
                subscription_id STRING NOT NULL,
                usage_date DATE,
                pretax_cost DECIMAL(38, 12) NOT NULL,
                currency STRING NOT NULL,
                dimensions JSONB NOT NULL,
                source_row_hash STRING NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_azure_cost_records_ingestion
            ON azure_cost_records (ingestion_id)
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_azure_cost_records_tenant_date
            ON azure_cost_records (tenant_id, usage_date)
            """
        )
    )
