import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OPENAPI_PATH = ROOT / "docs/api/azure-cost-query.openapi.json"
MAPPING_PATH = ROOT / "docs/api/azure-cost-query-mapping.json"
CASES_PATH = ROOT / "docs/api/azure-cost-query-contract-cases.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class AzureCostContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.openapi = load_json(OPENAPI_PATH)
        cls.mapping = load_json(MAPPING_PATH)
        cls.cases = load_json(CASES_PATH)

    def test_openapi_defines_subscription_query_and_fixed_version(self) -> None:
        path = "/subscriptions/{subscriptionId}/providers/Microsoft.CostManagement/query"
        operation = self.openapi["paths"][path]["post"]
        parameters = {item["name"]: item for item in operation["parameters"]}

        self.assertEqual(self.openapi["openapi"], "3.1.0")
        self.assertEqual(parameters["api-version"]["schema"]["const"], "2025-03-01")
        self.assertIn("200", operation["responses"])
        self.assertIn("400", operation["responses"])
        self.assertIn("401", operation["responses"])
        self.assertIn("403", operation["responses"])
        self.assertIn("404", operation["responses"])
        self.assertIn("429", operation["responses"])
        self.assertIn("500", operation["responses"])
        self.assertTrue(parameters["Authorization"]["required"])
        self.assertEqual(operation["security"], [{"SimulatedBearer": []}])
        self.assertEqual(
            set(parameters["X-Fake-Azure-Scenario"]["schema"]["enum"]),
            {
                "normal",
                "rate-limit",
                "server-error",
                "timeout",
                "empty-page",
                "invalid-data",
            },
        )

    def test_mapping_only_references_columns_present_in_fixture(self) -> None:
        fixture = ROOT / self.mapping["sourceFixture"]
        with fixture.open(encoding="utf-8-sig", newline="") as source:
            columns = set(next(csv.reader(source)))

        mapped = {self.mapping["scope"]["sourceColumn"]}
        mapped.update(item["sourceColumn"] for item in self.mapping["metrics"].values())
        mapped.update(item["sourceColumn"] for item in self.mapping["dimensions"].values())
        mapped.update(item["sourceColumn"] for item in self.mapping["systemColumns"].values())
        mapped.add(self.mapping["tags"]["sourceColumn"])

        self.assertEqual(mapped - columns, set())

    def test_success_example_rows_match_declared_columns(self) -> None:
        path = "/subscriptions/{subscriptionId}/providers/Microsoft.CostManagement/query"
        example = self.openapi["paths"][path]["post"]["responses"]["200"]["content"][
            "application/json"
        ]["example"]
        properties = example["properties"]

        self.assertTrue(properties["columns"])
        self.assertTrue(all(len(row) == len(properties["columns"]) for row in properties["rows"]))
        self.assertEqual(properties["columns"][-1], {"name": "Currency", "type": "String"})

    def test_contract_cases_cover_required_behaviors(self) -> None:
        cases = self.cases["cases"]
        ids = [case["id"] for case in cases]
        purposes = {case["purpose"] for case in cases}
        required = {
            "aggregation-and-grouping",
            "dimension-filter",
            "tag-filter",
            "pagination-intermediate",
            "pagination-last",
            "empty-result",
            "scope-error",
            "validation-error",
            "version-error",
            "pagination-error",
            "authentication-error",
            "authorization-error",
            "retryable-error",
            "timeout-simulation",
            "empty-page-simulation",
            "invalid-data-simulation",
        }

        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(required - purposes, set())

    def test_all_request_references_resolve(self) -> None:
        cases = {case["id"]: case for case in self.cases["cases"]}
        for case in cases.values():
            request_ref = case.get("requestRef")
            if request_ref:
                self.assertIn(request_ref, cases)
                self.assertIn("request", cases[request_ref])

    def test_custom_timeframes_always_define_a_period(self) -> None:
        for case in self.cases["cases"]:
            if case["expectedStatus"] != 200:
                continue
            request = case.get("request")
            if request and request.get("timeframe") == "Custom":
                self.assertEqual(set(request["timePeriod"]), {"from", "to"})

    def test_case_dimensions_and_tags_exist_in_mapping(self) -> None:
        dimensions = set(self.mapping["dimensions"])
        tags = set(self.mapping["tags"]["supportedNames"])

        def walk_filter(node):
            if not node:
                return
            for conjunction in ("and", "or"):
                for child in node.get(conjunction, []):
                    yield from walk_filter(child)
            if "dimensions" in node:
                yield "Dimension", node["dimensions"]["name"]
            if "tags" in node:
                yield "Tag", node["tags"]["name"]

        for case in self.cases["cases"]:
            if case["expectedStatus"] != 200:
                continue
            request = case.get("request")
            if not request:
                continue
            dataset = request["dataset"]
            names = [(item["type"], item["name"]) for item in dataset.get("grouping", [])]
            names.extend(walk_filter(dataset.get("filter")))
            for item_type, name in names:
                self.assertIn(name, dimensions if item_type == "Dimension" else tags)


if __name__ == "__main__":
    unittest.main()
