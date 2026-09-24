from sqlalchemy import text


transactional = False


def upgrade(connection) -> None:
    connection.execute(
        text(
            """
            ALTER TABLE azure_cost_records
                ADD COLUMN IF NOT EXISTS resource_id STRING,
                ADD COLUMN IF NOT EXISTS resource_name STRING,
                ADD COLUMN IF NOT EXISTS resource_group_conflicts JSONB
            """
        )
    )
    connection.execute(
        text(
            """
            WITH extracted AS (
                SELECT
                    id,
                    NULLIF(dimensions->>'ResourceId', '') AS resource_id,
                    NULLIF(dimensions->>'ResourceName', '') AS resource_name
                FROM azure_cost_records
            )
            UPDATE azure_cost_records AS records
            SET resource_id = COALESCE(records.resource_id, extracted.resource_id),
                resource_name = COALESCE(records.resource_name, extracted.resource_name)
            FROM extracted
            WHERE records.id = extracted.id
              AND (records.resource_id IS NULL OR records.resource_name IS NULL)
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_azure_cost_records_resource_id
            ON azure_cost_records (tenant_id, resource_id)
            """
        )
    )
