from sqlalchemy import text


def upgrade(connection) -> None:
    connection.execute(
        text(
            """
            ALTER TABLE azure_cost_records
                ADD COLUMN IF NOT EXISTS billing_account_id STRING,
                ADD COLUMN IF NOT EXISTS subscription_name STRING,
                ADD COLUMN IF NOT EXISTS resource_group STRING,
                ADD COLUMN IF NOT EXISTS service_name STRING,
                ADD COLUMN IF NOT EXISTS project STRING,
                ADD COLUMN IF NOT EXISTS consumed_quantity DECIMAL(38, 12),
                ADD COLUMN IF NOT EXISTS consumed_unit STRING,
                ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '{}'::JSONB
            """
        )
    )
    connection.execute(
        text(
            """
            UPDATE azure_cost_records
            SET resource_group = COALESCE(
                    resource_group,
                    dimensions->>'ResourceGroup',
                    dimensions->>'ResourceGroupName',
                    dimensions->>'x_ResourceGroupName'
                ),
                service_name = COALESCE(
                    service_name,
                    dimensions->>'ServiceName',
                    dimensions->>'MeterCategory',
                    dimensions->>'ServiceCategory'
                ),
                project = COALESCE(project, dimensions->>'Project')
            WHERE resource_group IS NULL
               OR service_name IS NULL
               OR project IS NULL
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_azure_cost_records_scope_date
            ON azure_cost_records (tenant_id, subscription_id, usage_date)
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_azure_cost_records_resource_group
            ON azure_cost_records (tenant_id, resource_group)
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_azure_cost_records_service
            ON azure_cost_records (tenant_id, service_name)
            """
        )
    )
