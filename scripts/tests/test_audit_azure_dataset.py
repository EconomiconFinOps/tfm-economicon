import csv
import json
import tempfile
import unittest
import zipfile
from decimal import Decimal
from pathlib import Path

from scripts.audit_azure_dataset import audit_archive, is_safe_entry, write_fixtures


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIRECTORY = REPOSITORY_ROOT / "fixtures" / "azure-cost"
AUDIT_REPORT = REPOSITORY_ROOT / "docs" / "data" / "azure-dataset-audit.json"
EXPECTED_ARCHIVE_SHA256 = (
    "d7769d9e759b5968a68affcb364235ad938a705168c546ab86cad5bbb27ff607"
)


class AuditAzureDatasetTests(unittest.TestCase):
    def test_profiles_csv_and_preserves_public_fixture_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "dataset.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(
                    "cost.csv",
                    "Date,AccountOwnerEmail,SubscriptionId,CostInBillingCurrency,Currency\n"
                    "06/01/2024,owner@example.com,ed570627-0265-4620-bb42-bae06bcfa914,1.5,USD\n"
                    "06/02/2024,,,2.5,USD\n",
                )

            report, fixtures = audit_archive(archive_path, sample_size=2)

            self.assertEqual(report["totals"]["rows"], 2)
            self.assertEqual(report["totals"]["malformed_rows"], 0)
            self.assertEqual(report["entries"][0]["date_ranges"]["Date"]["min"], "2024-06-01")
            self.assertEqual(report["entries"][0]["null_counts"]["SubscriptionId"], 1)
            self.assertEqual(
                report["entries"][0]["numeric_stats"]["CostInBillingCurrency"]["negative"], 0
            )
            self.assertEqual(report["entries"][0]["cardinalities"]["SubscriptionId"], 1)

            output = root / "fixtures"
            write_fixtures(fixtures, output, report)
            with (output / "cost.sample.csv").open(encoding="utf-8", newline="") as fixture:
                rows = list(csv.DictReader(fixture))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["AccountOwnerEmail"], "owner@example.com")
            self.assertEqual(
                rows[0]["SubscriptionId"], "ed570627-0265-4620-bb42-bae06bcfa914"
            )

    def test_sampling_is_deterministic_and_limited(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "dataset.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(
                    "cost.csv",
                    "SubscriptionId,CostInBillingCurrency\n"
                    + "".join(f"subscription-{index},{index}\n" for index in range(20)),
                )

            first_report, first_fixtures = audit_archive(archive_path, sample_size=5)
            second_report, second_fixtures = audit_archive(archive_path, sample_size=5)

            self.assertEqual(first_report, second_report)
            self.assertEqual(first_fixtures, second_fixtures)
            self.assertEqual(len(first_fixtures["cost.csv"]["rows"]), 5)

    def test_unsafe_archive_paths_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "dataset.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../cost.csv", "CostInBillingCurrency\n1\n")

            report, _ = audit_archive(archive_path)

            self.assertFalse(is_safe_entry("../cost.csv"))
            self.assertFalse(is_safe_entry("/cost.csv"))
            self.assertIn("unsafe entry path: ../cost.csv", report["archive"]["issues"])

    def test_malformed_rows_are_detected_and_excluded_from_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "dataset.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(
                    "cost.csv",
                    "SubscriptionId,CostInBillingCurrency\nvalid,1\ninvalid,2,extra\n",
                )

            report, fixtures = audit_archive(archive_path, sample_size=10)

            self.assertEqual(report["totals"]["rows"], 2)
            self.assertEqual(report["totals"]["malformed_rows"], 1)
            self.assertEqual(fixtures["cost.csv"]["rows"], [["valid", "1"]])

    def test_negative_zero_and_positive_costs_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "dataset.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(
                    "cost.csv", "CostInBillingCurrency\n-4.25\n0\n8.50\n"
                )

            report, fixtures = audit_archive(archive_path, sample_size=3)
            stats = report["entries"][0]["numeric_stats"]["CostInBillingCurrency"]

            self.assertEqual(stats["negative"], 1)
            self.assertEqual(stats["zero"], 1)
            self.assertEqual(stats["min"], "-4.25")
            self.assertEqual(stats["max"], "8.50")
            self.assertEqual(fixtures["cost.csv"]["rows"], [["-4.25"], ["0"], ["8.50"]])

    def test_versioned_fixtures_match_manifest_and_audited_source(self) -> None:
        manifest = json.loads((FIXTURES_DIRECTORY / "manifest.json").read_text("utf-8"))
        report = json.loads(AUDIT_REPORT.read_text("utf-8"))

        self.assertEqual(manifest["source_release"], "v14")
        self.assertEqual(manifest["source_archive_sha256"], EXPECTED_ARCHIVE_SHA256)
        self.assertEqual(report["archive"]["sha256"], EXPECTED_ARCHIVE_SHA256)
        self.assertEqual(report["archive"]["entry_count"], 11)
        self.assertEqual(report["totals"]["rows"], 1_295_308)
        self.assertEqual(report["archive"]["issues"], [])
        self.assertEqual(report["totals"]["malformed_rows"], 0)
        self.assertEqual(len(manifest["files"]), 11)
        self.assertIn("public values published by Microsoft", manifest["transformation"])

        source_entries = {entry["name"]: entry for entry in report["entries"]}
        versioned_csvs = {path.name for path in FIXTURES_DIRECTORY.glob("*.csv")}
        manifest_csvs = {fixture["path"] for fixture in manifest["files"]}
        self.assertEqual(versioned_csvs, manifest_csvs)

        for fixture in manifest["files"]:
            with self.subTest(fixture=fixture["path"]):
                source_entry = source_entries[fixture["source_entry"]]
                with (FIXTURES_DIRECTORY / fixture["path"]).open(
                    encoding="utf-8", newline=""
                ) as source:
                    reader = csv.DictReader(source)
                    rows = list(reader)

                self.assertEqual(reader.fieldnames, source_entry["columns"])
                self.assertEqual(len(rows), fixture["rows"])
                self.assertLessEqual(len(rows), 50)
                self.assertLessEqual(len(rows), source_entry["row_count"])

    def test_canonical_fixture_retains_negative_and_zero_public_costs(self) -> None:
        with (FIXTURES_DIRECTORY / "EA-Cost-Actual.sample.csv").open(
            encoding="utf-8", newline=""
        ) as source:
            rows = list(csv.DictReader(source))

        amounts = [Decimal(row["CostInBillingCurrency"]) for row in rows]
        self.assertEqual(len(rows), 50)
        self.assertTrue(any(amount < 0 for amount in amounts))
        self.assertTrue(any(amount == 0 for amount in amounts))
        self.assertTrue(any(amount > 0 for amount in amounts))
        self.assertTrue(any(row["SubscriptionId"] for row in rows))

    def test_microsoft_mit_license_is_versioned(self) -> None:
        license_text = (
            FIXTURES_DIRECTORY / "LICENSE.microsoft-finops-toolkit.txt"
        ).read_text(encoding="utf-8")

        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) Microsoft Corporation", license_text)


if __name__ == "__main__":
    unittest.main()
