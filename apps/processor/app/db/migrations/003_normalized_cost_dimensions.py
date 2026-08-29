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
            WITH extracted AS (
                SELECT
                    id,
                    NULLIF(dimensions->>'BillingAccountId', '') AS billing_account_id,
                    COALESCE(
                        NULLIF(dimensions->>'SubscriptionName', ''),
                        NULLIF(dimensions->>'SubAccountName', '')
                    ) AS subscription_name,
                    COALESCE(
                        NULLIF(dimensions->>'ResourceGroup', ''),
                        NULLIF(dimensions->>'ResourceGroupName', ''),
                        NULLIF(dimensions->>'x_ResourceGroupName', '')
                    ) AS resource_group,
                    COALESCE(
                        NULLIF(dimensions->>'ServiceName', ''),
                        NULLIF(dimensions->>'MeterCategory', ''),
                        NULLIF(dimensions->>'ServiceCategory', '')
                    ) AS service_name,
                    NULLIF(dimensions->>'Project', '') AS project,
                    COALESCE(
                        NULLIF(dimensions->>'ConsumedQuantity', ''),
                        NULLIF(dimensions->>'UsageQuantity', ''),
                        NULLIF(dimensions->>'Quantity', '')
                    ) AS consumed_quantity,
                    COALESCE(
                        NULLIF(dimensions->>'ConsumedUnit', ''),
                        NULLIF(dimensions->>'UnitOfMeasure', ''),
                        NULLIF(dimensions->>'Unit', '')
                    ) AS consumed_unit,
                    COALESCE(
                        NULLIF(dimensions->>'CostCenter', ''),
                        NULLIF(dimensions->>'costcenter', '')
                    ) AS tag_cost_center,
                    COALESCE(
                        NULLIF(dimensions->>'env', ''),
                        NULLIF(dimensions->>'Environment', '')
                    ) AS tag_environment,
                    COALESCE(
                        NULLIF(dimensions->>'org', ''),
                        NULLIF(dimensions->>'Organization', '')
                    ) AS tag_organization
                FROM azure_cost_records
            ),
            backfill AS (
                SELECT
                    id,
                    billing_account_id,
                    subscription_name,
                    resource_group,
                    service_name,
                    project,
                    consumed_quantity,
                    consumed_unit,
                    CASE
                        WHEN tag_cost_center IS NULL THEN '{}'::JSONB
                        ELSE jsonb_build_object('cost_center', tag_cost_center)
                    END
                    || CASE
                        WHEN project IS NULL THEN '{}'::JSONB
                        ELSE jsonb_build_object('project', project)
                    END
                    || CASE
                        WHEN tag_environment IS NULL THEN '{}'::JSONB
                        ELSE jsonb_build_object('environment', tag_environment)
                    END
                    || CASE
                        WHEN tag_organization IS NULL THEN '{}'::JSONB
                        ELSE jsonb_build_object('organization', tag_organization)
                    END AS tags
                FROM extracted
            )
            UPDATE azure_cost_records AS records
            SET billing_account_id = COALESCE(
                    records.billing_account_id,
                    backfill.billing_account_id
                ),
                subscription_name = COALESCE(
                    records.subscription_name,
                    backfill.subscription_name
                ),
                resource_group = COALESCE(records.resource_group, backfill.resource_group),
                service_name = COALESCE(records.service_name, backfill.service_name),
                project = COALESCE(records.project, backfill.project),
                consumed_quantity = COALESCE(
                    records.consumed_quantity,
                    CASE
                        WHEN backfill.consumed_quantity IS NOT NULL
                         AND backfill.consumed_unit IS NOT NULL
                        THEN backfill.consumed_quantity::DECIMAL(38, 12)
                    END
                ),
                consumed_unit = COALESCE(
                    records.consumed_unit,
                    CASE
                        WHEN backfill.consumed_quantity IS NOT NULL
                         AND backfill.consumed_unit IS NOT NULL
                        THEN backfill.consumed_unit
                    END
                ),
                tags = CASE
                    WHEN records.tags IS NULL OR records.tags = '{}'::JSONB
                    THEN backfill.tags
                    ELSE records.tags
                END
            FROM backfill
            WHERE records.id = backfill.id
              AND (
                   records.billing_account_id IS NULL
                OR records.subscription_name IS NULL
                OR records.resource_group IS NULL
                OR records.service_name IS NULL
                OR records.project IS NULL
                OR records.consumed_quantity IS NULL
                OR records.consumed_unit IS NULL
                OR records.tags IS NULL
                OR records.tags = '{}'::JSONB
              )
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
