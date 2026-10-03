"""Versioned rules for metadata compliance, not a corporate ownership catalog."""

POLICY_VERSION = "economicon-minimum-v1"
REQUIRED_TAGS = ("owner", "environment", "application", "cost_center", "project")
INVALID_VALUES = ("unknown", "n/a", "null", "none", "true", "false", "undefined", "unassigned", "-")
ENVIRONMENTS = ("dev", "development", "test", "testing", "staging", "stage", "prod", "production")


def tag_rule_sql(key: str) -> str:
    # Only closed policy constants may enter SQL. Request data never enters here.
    if key not in REQUIRED_TAGS:
        raise ValueError("Unknown policy tag")
    value = f"regexp_replace(tags ->> '{key}', '^\\s+|\\s+$', '', 'g')"
    invalid = ", ".join(f"'{item}'" for item in INVALID_VALUES)
    if key == "environment":
        accepted = ", ".join(f"'{item}'" for item in ENVIRONMENTS)
        rule = f"lower({value}) IN ({accepted})"
    else:
        rule = f"{value} ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{{0,127}}$'"
    return (
        f"COALESCE(jsonb_typeof(tags -> '{key}') = 'string' "
        f"AND lower({value}) NOT IN ({invalid}) AND {rule}, FALSE)"
    )
