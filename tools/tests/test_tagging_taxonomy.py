"""Independent design-contract tests; synthetic catalogs do not prove approval."""

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "tagging_taxonomy.py"
SPEC = importlib.util.spec_from_file_location("tagging_taxonomy", MODULE_PATH)
taxonomy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(taxonomy)

POLICY = {
    "policy_version": "economicon-minimum-v1",
    "catalog_policy_version": "economicon-catalog-v1",
    "required_tags": ["owner", "environment", "application", "cost_center", "project"],
    "identifier_pattern": "^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$",
    "invalid_values": ["unknown", "n/a", "null", "none", "true", "false", "undefined", "unassigned", "-"],
    "environments": {"dev": "dev", "development": "dev", "test": "test", "testing": "test",
                     "staging": "staging", "stage": "staging", "prod": "prod", "production": "prod"},
}


def valid_tags():
    return {"owner": "team-a", "environment": "prod", "application": "app-a",
            "cost_center": "CC-17", "project": "project-a"}


def valid_catalog(status="example"):
    return {
        "schema_version": 1,
        "policy_version": "economicon-catalog-v1",
        "catalog_version": "synthetic-2026-10-10",
        "tenant_id": "tenant-a",
        "status": status,
        "approval_reference": "synthetic-only-approval" if status == "approved" else None,
        "valid_from": "2026-10-01",
        "valid_to": "2026-11-01",
        "values": {"owner": ["team-a", "team-without-unit"], "application": ["app-a"],
                   "cost_center": ["CC-17"], "project": ["project-a"], "organization_unit": ["unit-a"]},
        "owner_to_org_unit": {"team-a": "unit-a"},
    }


class TaggingTaxonomyTests(unittest.TestCase):
    def evaluate(self, tags=None, **kwargs):
        args = {"tenant_id": "tenant-a", "usage_date": "2026-10-10", "policy": POLICY}
        args.update(kwargs)
        return taxonomy.evaluate_tags(valid_tags() if tags is None else tags, **args)

    def test_syntactic_success_does_not_claim_catalog_or_organizational_approval(self):
        result = self.evaluate()
        self.assertTrue(result["minimum_compliant"])
        self.assertEqual(result["defects"], {})
        self.assertEqual(result["catalog_status"], "not_provided")
        self.assertIsNone(result["catalog_version"])
        self.assertIsNone(result["catalog_match"])
        self.assertIsNone(result["organizationally_valid"])
        self.assertIsNone(result["organization_unit"])

    def test_defects_are_distinct_and_do_not_coerce_nonstring_values(self):
        tags = {"environment": " ", "application": False, "cost_center": " UNKNOWN ", "project": "x/y"}
        result = self.evaluate(tags)
        self.assertFalse(result["minimum_compliant"])
        self.assertEqual(result["defects"], {"owner": "missing", "environment": "empty",
                                           "application": "type", "cost_center": "placeholder",
                                           "project": "invalid_value"})
        for value in (None, True, False, 123, 0.5, [], {}, ["team-a"]):
            with self.subTest(value=value):
                self.assertEqual(self.evaluate({**valid_tags(), "owner": value})["defects"], {"owner": "type"})

    def test_placeholder_comparison_is_case_insensitive_after_trim(self):
        for value in ("N/A", "null", "None", " true ", "FALSE", "undefined", "unassigned", "-"):
            with self.subTest(value=value):
                self.assertEqual(self.evaluate({**valid_tags(), "owner": value})["defects"], {"owner": "placeholder"})

    def test_ascii_identifier_boundaries_and_trim(self):
        for value in ("x", "A" * 128, "A-1_b.c:d", " team-a "):
            with self.subTest(valid=value):
                self.assertTrue(self.evaluate({**valid_tags(), "owner": value})["minimum_compliant"])
        for value in ("x" * 129, "-team", ".team", "équipe", "team a", "team/a", "team\na", "team@a"):
            with self.subTest(invalid=value):
                self.assertEqual(self.evaluate({**valid_tags(), "owner": value})["defects"], {"owner": "invalid_value"})

    def test_environment_aliases_are_explicit(self):
        for value in ("dev", "development", "test", "testing", "staging", "stage", "prod", "production",
                      "PROD", "Production", " DEV "):
            with self.subTest(environment=value):
                self.assertTrue(self.evaluate({**valid_tags(), "environment": value})["minimum_compliant"])
        for value in ("sandbox", "qa", "production-east"):
            with self.subTest(environment=value):
                self.assertEqual(self.evaluate({**valid_tags(), "environment": value})["defects"],
                                 {"environment": "invalid_value"})

    def test_optional_tags_and_alias_keys_cannot_replace_required_dimensions(self):
        for canonical, substitute in (("owner", "team"), ("owner", "organization_unit"),
                                      ("application", "project"), ("project", "application"),
                                      ("cost_center", "costcentre"), ("owner", "Owner")):
            with self.subTest(canonical=canonical, substitute=substitute):
                tags = valid_tags()
                value = tags.pop(canonical)
                tags[substitute] = value
                self.assertEqual(self.evaluate(tags)["defects"].get(canonical), "missing")
        result = self.evaluate({**valid_tags(), "organization_unit": "forged-unit", "team": "other-team"},
                               catalog=valid_catalog())
        self.assertEqual(result["organization_unit"], "unit-a")

    def test_example_catalog_reports_membership_without_approval(self):
        result = self.evaluate(catalog=valid_catalog())
        self.assertEqual(result["catalog_status"], "example")
        self.assertTrue(result["catalog_match"])
        self.assertIsNone(result["organizationally_valid"])
        self.assertEqual(result["organization_unit"], "unit-a")

    def test_approved_catalog_reports_true_or_false_but_does_not_verify_reference(self):
        catalog = valid_catalog("approved")
        self.assertTrue(self.evaluate(catalog=catalog)["organizationally_valid"])
        result = self.evaluate({**valid_tags(), "application": "app-b"}, catalog=catalog)
        self.assertTrue(result["minimum_compliant"])
        self.assertFalse(result["catalog_match"])
        self.assertFalse(result["organizationally_valid"])
        self.assertEqual(result["unknown_catalog_values"], ["application"])
        result = self.evaluate({**valid_tags(), "environment": "invalid"}, catalog=catalog)
        self.assertFalse(result["organizationally_valid"])
        self.assertEqual(result["unknown_catalog_values"], [])

    def test_catalog_membership_uses_case_sensitive_ids_and_independent_dimensions(self):
        tags = {**valid_tags(), "owner": "TEAM-A", "application": "project-a",
                "project": "app-a", "cost_center": "cc-17"}
        result = self.evaluate(tags, catalog=valid_catalog())
        self.assertEqual(result["unknown_catalog_values"], ["owner", "application", "cost_center", "project"])
        self.assertIsNone(result["organization_unit"])
        self.assertFalse(result["catalog_match"])
        self.assertTrue(result["minimum_compliant"])

    def test_only_syntactically_valid_values_are_reported_as_unknown_catalog_members(self):
        result = self.evaluate({"owner": "?", "environment": "prod", "application": "new-app",
                                "cost_center": "none", "project": None}, catalog=valid_catalog())
        self.assertEqual(result["unknown_catalog_values"], ["application"])
        self.assertIsNone(result["organization_unit"])

    def test_absent_explicit_owner_mapping_does_not_infer_unit(self):
        result = self.evaluate({**valid_tags(), "owner": "team-without-unit", "organization_unit": "unit-a"},
                               catalog=valid_catalog())
        self.assertTrue(result["catalog_match"])
        self.assertIsNone(result["organization_unit"])

    def test_draft_catalog_does_not_establish_membership_or_unit(self):
        result = self.evaluate({**valid_tags(), "application": "unknown-app"}, catalog=valid_catalog("draft"))
        self.assertEqual(result["catalog_status"], "draft")
        self.assertEqual(result["unknown_catalog_values"], [])
        for field in ("catalog_match", "organizationally_valid", "organization_unit"):
            self.assertIsNone(result[field])

    def test_validity_is_half_open_and_tenant_scoped(self):
        catalog = valid_catalog("approved")
        for usage_date in ("2026-10-01", "2026-10-31"):
            with self.subTest(usage_date=usage_date):
                self.assertTrue(self.evaluate(catalog=catalog, usage_date=usage_date)["organizationally_valid"])
        for kwargs in ({"usage_date": "2026-09-30"}, {"usage_date": "2026-11-01"},
                       {"tenant_id": "tenant-b"}, {"tenant_id": "TENANT-A"}):
            with self.subTest(kwargs=kwargs):
                result = self.evaluate(catalog=catalog, **kwargs)
                self.assertEqual(result["catalog_status"], "not_applicable")
                self.assertEqual(result["catalog_version"], "synthetic-2026-10-10")
                self.assertEqual(result["unknown_catalog_values"], [])
                for field in ("catalog_match", "organizationally_valid", "organization_unit"):
                    self.assertIsNone(result[field])
        catalog["valid_to"] = None
        self.assertTrue(self.evaluate(catalog=catalog, usage_date="2099-01-01")["organizationally_valid"])

    def test_input_shape_and_dates_are_not_silently_coerced(self):
        for usage_date in ("20261010", "2026-2-01", "2026-02-30", "2026-10-10T00:00:00", None, 20261010):
            with self.subTest(usage_date=usage_date), self.assertRaises(ValueError):
                self.evaluate(usage_date=usage_date)
        for tenant in (None, "", " ", True, []):
            with self.subTest(tenant=tenant), self.assertRaises(ValueError):
                self.evaluate(tenant_id=tenant)
        for tags in ([], "owner=team-a", True):
            with self.subTest(tags=tags), self.assertRaises(ValueError):
                self.evaluate(tags)

    def test_evaluation_does_not_modify_input(self):
        tags = {**valid_tags(), "owner": " team-a ", "environment": "production"}
        catalog = valid_catalog()
        original = copy.deepcopy((tags, catalog, POLICY))
        result = self.evaluate(tags, catalog=catalog)
        self.assertTrue(result["catalog_match"])
        self.assertEqual((tags, catalog, POLICY), original)

    def test_same_policy_version_cannot_redefine_markers_or_environment_aliases(self):
        for mutation in ("remove-placeholder", "add-placeholder", "duplicate-placeholder",
                         "add-qa", "remove-alias", "change-alias-target"):
            with self.subTest(mutation=mutation):
                policy = copy.deepcopy(POLICY)
                if mutation == "remove-placeholder":
                    policy["invalid_values"].remove("unknown")
                elif mutation == "add-placeholder":
                    policy["invalid_values"].append("app-a")
                elif mutation == "duplicate-placeholder":
                    policy["invalid_values"].append("unknown")
                elif mutation == "add-qa":
                    policy["environments"]["qa"] = "test"
                elif mutation == "remove-alias":
                    del policy["environments"]["production"]
                else:
                    policy["environments"]["production"] = "dev"
                with self.assertRaises(ValueError):
                    self.evaluate(policy=policy)


class CatalogValidationTests(unittest.TestCase):
    def assert_invalid(self, field, value):
        catalog = valid_catalog()
        catalog[field] = value
        with self.assertRaises(ValueError):
            taxonomy.validate_catalog(catalog, POLICY)

    def test_missing_fields_and_wrong_metadata_are_rejected(self):
        for field in valid_catalog():
            with self.subTest(missing=field):
                catalog = valid_catalog()
                del catalog[field]
                with self.assertRaises(ValueError):
                    taxonomy.validate_catalog(catalog, POLICY)
        for field, value in (("schema_version", True), ("schema_version", 2), ("schema_version", "1"),
                             ("policy_version", "economicon-minimum-v1"), ("catalog_version", ""),
                             ("tenant_id", 1), ("tenant_id", " tenant-a"), ("status", "validated"),
                             ("status", []), ("status", {}),
                             ("approval_reference", " "), ("approval_reference", False),
                             ("valid_from", "2026-10-32"), ("valid_to", "2026-10-01"),
                             ("valid_to", "2026-09-30"), ("valid_to", "")):
            with self.subTest(field=field, value=value):
                self.assert_invalid(field, value)

    def test_approval_requires_a_nonblank_reference(self):
        for reference in (None, "", " ", 12):
            with self.subTest(reference=reference):
                catalog = valid_catalog("approved")
                catalog["approval_reference"] = reference
                with self.assertRaises(ValueError):
                    taxonomy.validate_catalog(catalog, POLICY)

    def test_missing_or_extra_dimensions_are_rejected(self):
        for dimension in ("owner", "application", "cost_center", "project", "organization_unit"):
            with self.subTest(missing=dimension):
                catalog = valid_catalog()
                del catalog["values"][dimension]
                with self.assertRaises(ValueError):
                    taxonomy.validate_catalog(catalog, POLICY)
        self.assert_invalid("values", {**valid_catalog()["values"], "team": []})
        self.assert_invalid("values", [])

    def test_invalid_and_duplicate_catalog_identifiers_are_rejected(self):
        for identifiers in (["app-a", "app-a"], [" app-a"], ["unknown"], ["N/A"], [False],
                            [1], [None], [["app-a"]], [{}], ["a" * 129], "app-a"):
            with self.subTest(identifiers=identifiers):
                catalog = valid_catalog()
                catalog["values"]["application"] = identifiers
                with self.assertRaises(ValueError):
                    taxonomy.validate_catalog(catalog, POLICY)
        catalog = valid_catalog()
        catalog["values"]["application"] = ["app-a", "APP-A"]
        taxonomy.validate_catalog(catalog, POLICY)

    def test_mapping_must_reference_existing_distinct_catalog_dimensions(self):
        for mapping in ([], {"missing-team": "unit-a"}, {"team-a": "missing-unit"},
                        {"team-a": "app-a"}, {"team-a": None}, {"team-a": []}):
            with self.subTest(mapping=mapping):
                self.assert_invalid("owner_to_org_unit", mapping)
        catalog = valid_catalog()
        catalog["owner_to_org_unit"] = {}
        taxonomy.validate_catalog(catalog, POLICY)

    def test_malformed_catalog_is_rejected_even_when_tenant_is_inapplicable(self):
        catalog = valid_catalog()
        catalog["schema_version"] = False
        with self.assertRaises(ValueError):
            taxonomy.evaluate_tags(valid_tags(), tenant_id="other", usage_date="2026-10-10",
                                   catalog=catalog, policy=POLICY)


class FixtureCliTests(unittest.TestCase):
    def fixture(self):
        return {"catalog": valid_catalog(), "cases": [{"name": "documented-example",
                "tenant_id": "tenant-a", "usage_date": "2026-10-10", "tags": valid_tags(),
                "expected": {"minimum_compliant": True, "catalog_status": "example",
                             "catalog_match": True, "organizationally_valid": None}}]}

    def test_cli_success_mismatch_and_invalid_input_have_distinct_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            policy_path = directory / "policy.json"
            case_path = directory / "cases.json"
            policy_path.write_text(json.dumps(POLICY), encoding="utf-8")
            fixture = self.fixture()
            command = [sys.executable, str(MODULE_PATH), "--policy", str(policy_path), "--cases", str(case_path)]
            for expected, code, marker in ((True, 0, "PASS documented-example"),
                                          (False, 1, "FAIL documented-example"),
                                          (1, 1, "FAIL documented-example")):
                with self.subTest(expected=expected):
                    fixture["cases"][0]["expected"]["minimum_compliant"] = expected
                    case_path.write_text(json.dumps(fixture), encoding="utf-8")
                    result = subprocess.run(command, cwd=directory, text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, code, result.stderr)
                    self.assertIn(marker, result.stdout)
            case_path.write_text("not json", encoding="utf-8")
            result = subprocess.run(command, cwd=directory, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("ERROR:", result.stderr)

    def test_fixture_subset_comparison_rejects_unknown_keys_and_compares_all_cases(self):
        fixture = self.fixture()
        fixture["cases"][0]["expected"]["unsupported_result"] = None
        second = copy.deepcopy(fixture["cases"][0])
        second["name"] = "second-case"
        second["expected"] = {"minimum_compliant": True}
        fixture["cases"].append(second)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertFalse(taxonomy.run_cases(fixture, POLICY))
        self.assertIn("FAIL documented-example", stream.getvalue())
        self.assertIn("PASS second-case", stream.getvalue())

    def test_duplicate_json_keys_are_rejected_at_all_nesting_levels(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            policy_path = directory / "policy.json"
            case_path = directory / "cases.json"
            policy_path.write_text(json.dumps(POLICY), encoding="utf-8")
            fixture_json = json.dumps(self.fixture())
            cases_with_duplicates = (
                fixture_json.replace('"team-a": "unit-a"', '"team-a": "unit-a", "team-a": "other-unit"'),
                fixture_json.replace('"owner": "team-a"', '"owner": "team-a", "owner": "other-team"'),
            )
            for invalid_json in cases_with_duplicates:
                with self.subTest(document=invalid_json):
                    case_path.write_text(invalid_json, encoding="utf-8")
                    with contextlib.redirect_stderr(io.StringIO()) as output:
                        code = taxonomy.main(["--policy", str(policy_path), "--cases", str(case_path)])
                    self.assertEqual(code, 2)
                    self.assertIn("duplicate JSON key", output.getvalue())
            policy_path.write_text(json.dumps(POLICY).replace('"policy_version":',
                                   '"policy_version": "bad", "policy_version":'), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                taxonomy.load_policy(policy_path)

    def test_empty_expectations_empty_cases_and_duplicate_names_cannot_pass_vacuously(self):
        for change in ("empty-expectations", "empty-cases", "duplicate-name"):
            with self.subTest(change=change):
                fixture = self.fixture()
                if change == "empty-expectations":
                    fixture["cases"][0]["expected"] = {}
                elif change == "empty-cases":
                    fixture["cases"] = []
                else:
                    fixture["cases"].append(copy.deepcopy(fixture["cases"][0]))
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
                    taxonomy.run_cases(fixture, POLICY)


if __name__ == "__main__":
    unittest.main()
