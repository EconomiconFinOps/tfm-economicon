"""Cada indicador de JUP-130 es su propia fuente: no se anotan entre sí ni forman una serie comparable."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("economicon_memory_indicators_runs", ROOT / "tools" / "memory-indicators.py")
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

DASHBOARD = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_for_jup130_runs", ROOT / "tools" / "evaluation-dashboard.py")
dashboard = importlib.util.module_from_spec(DASHBOARD)
sys.modules[DASHBOARD.name] = dashboard
DASHBOARD.loader.exec_module(dashboard)

EXPECTED_SOURCES = {"anomalies": "JUP-130-anomalies", "data": "JUP-130-data", "ai-cost": "JUP-130-ai-cost"}


def reports() -> dict[str, dict]:
    chat = {"request_id": "gen-1", "call_type": "acompletion", "status": "success", "spend": 0.5, "model": "m",
            "startTime": "2026-10-15T10:00:00Z", "metadata": {}}
    return {
        "anomalies": tool.anomaly_report(date(2026, 10, 30), commit=None, run_at="2026-10-21T10:00:00Z")[0],
        "data": tool.data_report(fetch=None, reference_date_from_api=None, reference=date(2026, 10, 30), commit=None,
                                 run_at="2026-10-21T10:01:00Z")[0],
        "ai-cost": tool.ai_cost_report([chat], date(2026, 10, 12), date(2026, 10, 21), None, 10, commit=None,
                                       run_at="2026-10-21T10:02:00Z")[0],
    }


class OneSourcePerIndicator(unittest.TestCase):
    def test_each_indicator_has_its_own_source(self):
        self.assertEqual({name: report["run"]["source"] for name, report in reports().items()}, EXPECTED_SOURCES)

    def test_the_three_sources_are_distinct_and_share_the_jup_130_prefix(self):
        sources = [report["run"]["source"] for report in reports().values()]
        self.assertEqual(len(set(sources)), 3)
        self.assertTrue(all(source.startswith("JUP-130-") for source in sources))

    def test_the_sources_are_valid_identifiers_for_the_contract(self):
        for report in reports().values():
            dashboard.adapt_rows_v1(report)

    def test_no_two_runs_share_a_comparability_key(self):
        keys = []
        for report in reports().values():
            run, _ = dashboard.adapt_rows_v1(report)
            keys.append(dashboard.classify_run_row(run)["comparability_key"])
        self.assertEqual(len(set(keys)), 3)

    def test_the_anomaly_run_carries_the_fingerprint_of_its_labelled_events(self):
        run = reports()["anomalies"]["run"]
        self.assertRegex(run["suite_sha256"], r"^[0-9a-f]{64}$")

    def test_the_other_runs_carry_no_battery_fingerprint(self):
        for name in ("data", "ai-cost"):
            self.assertNotIn("suite_sha256", reports()[name]["run"], name)

    def test_each_run_keeps_its_own_identifier(self):
        ids = [report["run"]["run_id"] for report in reports().values()]
        self.assertEqual(len(set(ids)), 3)


if __name__ == "__main__":
    unittest.main()
