import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent))
import smoke


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.release = Path(self.temp.name)
        (self.release / "release.json").write_text(json.dumps({"api_port": 19457}))
        (self.release / ".env").write_text("DEMO_PASSWORD='synthetic-test-password'\n")
        self.responses = [None] * 4 + [{"access_token": "synthetic-token"},
                          {"totals": [{"amount": 1}], "data_status": "available"},
                          {"job_id": "12345678-1234-1234-1234-123456789abc"}]

    def tearDown(self):
        self.temp.cleanup()

    def test_full_journey_requires_real_completed_job(self):
        compose = Mock(side_effect=[None, "status\ncompleted\n"])
        with patch.object(smoke, "request", side_effect=self.responses):
            smoke.verify(self.release, compose)
        self.assertIn("app.run_azure_cost_ingestion", compose.call_args_list[0].args)
        self.assertIn("SELECT status FROM jobs", compose.call_args.args[-1])

    def test_empty_summary_fails_before_job_submission(self):
        self.responses[5] = {"totals": [], "data_status": "empty"}
        with patch.object(smoke, "request", side_effect=self.responses) as request:
            with self.assertRaises(RuntimeError):
                smoke.verify(self.release, Mock())
        self.assertEqual(request.call_count, 6)

    def test_invalid_job_id_never_reaches_sql(self):
        self.responses[6]["job_id"] = "'; DROP TABLE jobs; --"
        compose = Mock()
        with patch.object(smoke, "request", side_effect=self.responses):
            with self.assertRaises(ValueError):
                smoke.verify(self.release, compose)
        self.assertEqual(compose.call_count, 1)

    def test_failed_document_job_is_not_success(self):
        compose = Mock(side_effect=[None, "status\nfailed\n"])
        with patch.object(smoke, "request", side_effect=self.responses):
            with self.assertRaises(RuntimeError):
                smoke.verify(self.release, compose)


if __name__ == "__main__":
    unittest.main()
