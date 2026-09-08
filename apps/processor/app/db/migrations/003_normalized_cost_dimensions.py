import json

from sqlalchemy import text

from app.normalization.azure_cost import (
    _INDIVIDUAL_TAG_ALIASES,
    _canonical_tag_key,
    _parse_tag_map,
)


transactional = False


def _legacy_tags(dimensions) -> dict[str, str]:
    tags: dict[str, str] = {}
    source = {key.casefold(): value for key, value in dimensions.items()}
    # Legacy individual dimensions accepted numbers and precede serialized tags.
    for canonical, aliases in _INDIVIDUAL_TAG_ALIASES.items():
        for alias in aliases:
            value = source.get(alias.casefold())
            if value is not None and str(value).strip():
                tags.setdefault(canonical, str(value).strip())
    raw_tags = source.get("tags")
    if isinstance(raw_tags, str):
        for key, value in _parse_tag_map(raw_tags.strip()).items():
            canonical = _canonical_tag_key(key)
            if canonical:
                tags.setdefault(canonical, value)
    return tags


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
                         AND (records.consumed_unit IS NULL
                              OR records.consumed_unit = backfill.consumed_unit)
                        THEN backfill.consumed_quantity::DECIMAL(38, 12)
                    END
                ),
                consumed_unit = COALESCE(
                    records.consumed_unit,
                    CASE
                        WHEN backfill.consumed_quantity IS NOT NULL
                         AND backfill.consumed_unit IS NOT NULL
                         AND (records.consumed_quantity IS NULL
                              OR records.consumed_quantity =
                                 backfill.consumed_quantity::DECIMAL(38, 12))
                        THEN backfill.consumed_unit
                    END
                ),
                tags = backfill.tags || COALESCE(records.tags, '{}'::JSONB)
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
    last_id = None
    while True:
        rows = connection.execute(
            text(
                """
                SELECT id, dimensions
                FROM azure_cost_records
                """
                + ("WHERE id > :last_id " if last_id is not None else "")
                + "ORDER BY id LIMIT 1000"
            ),
            {"last_id": last_id} if last_id is not None else {},
        )
        found_rows = False
        for record_id, dimensions in rows:
            found_rows = True
            last_id = record_id
            tags = _legacy_tags(dimensions)
            if not tags:
                continue
            connection.execute(
                text(
                    """
                    UPDATE azure_cost_records
                    SET project = COALESCE(NULLIF(project, ''), :project),
                        tags = CAST(:tags AS JSONB) || COALESCE(tags, '{}'::JSONB)
                    WHERE id = :record_id
                    """
                ),
                {
                    "record_id": record_id,
                    "project": tags.get("project"),
                    "tags": json.dumps(tags),
                },
            )
        if not found_rows:
            break
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
