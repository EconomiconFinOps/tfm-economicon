"""JUP-015 reference evaluator; no ingestion or application runtime integration.

Input keys are already canonical. The evaluator never aliases keys, infers an
owner from an application, or treats a supplied approval reference as verified.
"""

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys


DEFAULT_POLICY = Path(__file__).resolve().parents[1] / "docs/finops/tagging-taxonomy.json"
CATALOG_DIMENSIONS = ("owner", "application", "cost_center", "project", "organization_unit")
TAG_DIMENSIONS = CATALOG_DIMENSIONS[:-1]
REQUIRED_TAGS = ("owner", "environment", "application", "cost_center", "project")
# A version identifies immutable behavior, not a configurable validation profile.
INVALID_VALUES_V1 = {"unknown", "n/a", "null", "none", "true", "false", "undefined", "unassigned", "-"}
ENVIRONMENTS_V1 = {
    "dev": "dev", "development": "dev", "test": "test", "testing": "test",
    "staging": "staging", "stage": "staging", "prod": "prod", "production": "prod",
}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_policy(path=DEFAULT_POLICY):
    """Read the versioned design contract without a working-directory dependency."""
    with Path(path).open(encoding="utf-8-sig") as stream:
        policy = json.load(stream, object_pairs_hook=_unique_object)
    _validate_policy(policy)
    return policy


def _validate_policy(policy):
    if not isinstance(policy, dict):
        raise ValueError("policy must be an object")
    if policy.get("policy_version") != "economicon-minimum-v1":
        raise ValueError("unsupported policy_version")
    if policy.get("catalog_policy_version") != "economicon-catalog-v1":
        raise ValueError("unsupported catalog_policy_version")
    if policy.get("required_tags") != list(REQUIRED_TAGS):
        raise ValueError("required_tags must contain the five canonical tags in order")
    if policy.get("identifier_pattern") != r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$":
        raise ValueError("unsupported identifier_pattern")
    invalid = policy.get("invalid_values")
    if (
        not isinstance(invalid, list)
        or any(not isinstance(value, str) for value in invalid)
        or len(invalid) != len(INVALID_VALUES_V1)
        or set(invalid) != INVALID_VALUES_V1
    ):
        raise ValueError("invalid_values must match the immutable v1 placeholder set")
    if policy.get("environments") != ENVIRONMENTS_V1:
        raise ValueError("environments must match the immutable v1 alias mapping")


def _get_policy(policy):
    if policy is None:
        return load_policy()
    _validate_policy(policy)
    return policy


def _iso_date(value, field):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError(f"{field} must be a YYYY-MM-DD string")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a real calendar date") from exc


def _nonblank_string(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")


def _identifier_valid(value, policy):
    return (
        isinstance(value, str)
        and re.fullmatch(policy["identifier_pattern"], value) is not None
        and value.casefold() not in {item.casefold() for item in policy["invalid_values"]}
    )


def validate_catalog(catalog, policy=None):
    """Raise ValueError for an invalid snapshot; approval claims are not verified.

    Validity is the half-open interval [valid_from, valid_to), with null valid_to
    denoting an open end. Mappings may be partial, but never dangling.
    """
    policy = _get_policy(policy)
    if not isinstance(catalog, dict):
        raise ValueError("catalog must be an object")
    required = {
        "schema_version", "policy_version", "catalog_version", "tenant_id", "status",
        "approval_reference", "valid_from", "valid_to", "values", "owner_to_org_unit",
    }
    missing = required - catalog.keys()
    if missing:
        raise ValueError(f"catalog is missing fields: {', '.join(sorted(missing))}")
    if type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1:
        raise ValueError("unsupported catalog schema_version")
    if catalog["policy_version"] != policy["catalog_policy_version"]:
        raise ValueError("unsupported catalog policy_version")
    for field in ("catalog_version", "tenant_id"):
        _nonblank_string(catalog[field], field)
        if catalog[field] != catalog[field].strip():
            raise ValueError(f"{field} must not contain surrounding whitespace")
    if catalog["status"] not in ("draft", "example", "approved"):
        raise ValueError("catalog status must be draft, example, or approved")
    approval = catalog["approval_reference"]
    if approval is not None:
        _nonblank_string(approval, "approval_reference")
    if catalog["status"] == "approved" and approval is None:
        raise ValueError("approved catalog requires approval_reference")
    start = _iso_date(catalog["valid_from"], "valid_from")
    if catalog["valid_to"] is not None and _iso_date(catalog["valid_to"], "valid_to") <= start:
        raise ValueError("catalog validity interval must be nonempty")
    values = catalog["values"]
    if not isinstance(values, dict) or set(values) != set(CATALOG_DIMENSIONS):
        raise ValueError("catalog values must contain exactly the five catalog dimensions")
    for dimension, identifiers in values.items():
        if not isinstance(identifiers, list):
            raise ValueError(f"values.{dimension} must be an array")
        if any(not _identifier_valid(value, policy) for value in identifiers):
            raise ValueError(f"values.{dimension} contains an invalid identifier")
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(f"values.{dimension} contains a duplicate identifier")
    mapping = catalog["owner_to_org_unit"]
    if not isinstance(mapping, dict):
        raise ValueError("owner_to_org_unit must be an object")
    for owner, unit in mapping.items():
        if owner not in values["owner"] or unit not in values["organization_unit"]:
            raise ValueError("owner_to_org_unit contains a dangling mapping")


def evaluate_tags(tags, *, tenant_id, usage_date, catalog=None, policy=None):
    """Evaluate syntax and, separately, an applicable catalog's membership.

    Unknown values are reported as canonical dimension names, in stable order.
    Optional tags do not replace any required tag or explicit catalog mapping.
    """
    policy = _get_policy(policy)
    if not isinstance(tags, dict):
        raise ValueError("tags must be a canonical object")
    _nonblank_string(tenant_id, "tenant_id")
    usage = _iso_date(usage_date, "usage_date")
    defects = {}
    normalized = {}
    invalid_values = {value.casefold() for value in policy["invalid_values"]}
    for key in policy["required_tags"]:
        if key not in tags:
            defects[key] = "missing"
        elif not isinstance(tags[key], str):
            defects[key] = "type"
        else:
            value = tags[key].strip()
            if not value:
                defects[key] = "empty"
            elif value.casefold() in invalid_values:
                defects[key] = "placeholder"
            elif key == "environment":
                value = value.lower()
                if value not in policy["environments"]:
                    defects[key] = "invalid_value"
                else:
                    normalized[key] = policy["environments"][value]
            elif not _identifier_valid(value, policy):
                defects[key] = "invalid_value"
            else:
                normalized[key] = value

    result = {
        "policy_version": policy["policy_version"],
        "minimum_compliant": not defects,
        "defects": defects,
        "catalog_policy_version": policy["catalog_policy_version"],
        "catalog_version": None,
        "catalog_status": "not_provided",
        "unknown_catalog_values": [],
        "catalog_match": None,
        "organizationally_valid": None,
        "organization_unit": None,
    }
    if catalog is None:
        return result
    validate_catalog(catalog, policy)
    result["catalog_version"] = catalog["catalog_version"]
    if (
        catalog["tenant_id"] != tenant_id
        or usage < _iso_date(catalog["valid_from"], "valid_from")
        or (catalog["valid_to"] is not None and usage >= _iso_date(catalog["valid_to"], "valid_to"))
    ):
        result["catalog_status"] = "not_applicable"
        return result
    result["catalog_status"] = catalog["status"]
    if catalog["status"] == "draft":
        return result
    unknown = [
        key for key in TAG_DIMENSIONS
        if key in normalized and normalized[key] not in catalog["values"][key]
    ]
    result["unknown_catalog_values"] = unknown
    result["catalog_match"] = not defects and not unknown
    if catalog["status"] == "approved":
        result["organizationally_valid"] = result["catalog_match"]
    if "owner" in normalized and "owner" not in unknown:
        result["organization_unit"] = catalog["owner_to_org_unit"].get(normalized["owner"])
    return result


def run_cases(document, policy):
    """Print one result per design fixture, returning False for any mismatch."""
    if not isinstance(document, dict) or not isinstance(document.get("cases"), list) or not document["cases"]:
        raise ValueError("fixture document must contain a nonempty cases array")
    catalog = document.get("catalog")
    if catalog is not None:
        validate_catalog(catalog, policy)
    names = set()
    passed = True
    for case in document["cases"]:
        if not isinstance(case, dict):
            raise ValueError("each fixture case must be an object")
        name = case.get("name")
        _nonblank_string(name, "case.name")
        if name in names:
            raise ValueError("case names must be unique")
        names.add(name)
        if not isinstance(case.get("expected"), dict) or not case["expected"]:
            raise ValueError(f"case {name}: expected must be a nonempty object")
        if not {"tags", "tenant_id", "usage_date"} <= case.keys():
            raise ValueError(f"case {name}: tags, tenant_id, and usage_date are required")
        result = evaluate_tags(
            case["tags"], tenant_id=case["tenant_id"], usage_date=case["usage_date"],
            catalog=catalog, policy=policy,
        )
        mismatches = [
            key for key, expected in case["expected"].items()
            if key not in result or result[key] != expected or type(result[key]) is not type(expected)
        ]
        print(f"{'FAIL' if mismatches else 'PASS'} {name}")
        for key in mismatches:
            print(f"  {key}: expected {case['expected'][key]!r}, got {result.get(key)!r}")
        passed = passed and not mismatches
    return passed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True, help="JSON file with catalog and reference cases")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY, help="versioned taxonomy JSON policy")
    args = parser.parse_args(argv)
    try:
        policy = load_policy(args.policy)
        with args.cases.open(encoding="utf-8-sig") as stream:
            document = json.load(stream, object_pairs_hook=_unique_object)
        return 0 if run_cases(document, policy) else 1
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
