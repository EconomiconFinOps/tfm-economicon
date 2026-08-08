import csv
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.audit_azure_dataset import audit_archive, write_fixtures


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


if __name__ == "__main__":
    unittest.main()
