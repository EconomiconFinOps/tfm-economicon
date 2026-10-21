"""Medición de la calidad del detector de anomalías de `tools/memory-indicators.py` (JUP-130, grupo 2)."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools" / "memory-indicators.py"
SPEC = importlib.util.spec_from_file_location("economicon_memory_indicators", TOOL_PATH)
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

DASHBOARD = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_for_jup130", ROOT / "tools" / "evaluation-dashboard.py")
dashboard = importlib.util.module_from_spec(DASHBOARD)
sys.modules[DASHBOARD.name] = dashboard
DASHBOARD.loader.exec_module(dashboard)

EXPECTED = json.loads((ROOT / "docs" / "demo" / "JUP-107" / "esperados-anomalias.json").read_text("utf-8"))


def event(identifier, service, start, designed=True):
    return {"id": identifier, "service": service, "start_date": start, "nature": "x", "detectable_by_design": designed}


def episode(service, start):
    return SimpleNamespace(service=service, start_date=date.fromisoformat(start))


def row(report, metric_id, behavior="all"):
    found = [r for r in report["results"] if r["metric_id"] == metric_id and r["behavior"] == behavior]
    assert len(found) == 1, (metric_id, behavior, found)
    return found[0]


class MatchEvents(unittest.TestCase):
    def match(self, events, episodes, tolerance=3):
        return tool.match_events(events, episodes, tolerance)

    def test_an_episode_on_the_same_day_detects_the_event_with_no_delay(self):
        result = self.match([event("EV-1", "Compute", "2026-09-09")], [episode("Compute", "2026-09-09")])
        self.assertEqual((result.tp, result.fp, result.fn), (1, 0, 0))
        self.assertEqual(result.delays, {"EV-1": 0})

    def test_the_tolerance_is_inclusive_at_three_days(self):
        result = self.match([event("EV-1", "Compute", "2026-09-09")], [episode("Compute", "2026-09-12")])
        self.assertEqual((result.tp, result.delays), (1, {"EV-1": 3}))

    def test_four_days_late_is_a_miss_and_a_false_positive(self):
        result = self.match([event("EV-1", "Compute", "2026-09-09")], [episode("Compute", "2026-09-13")])
        self.assertEqual((result.tp, result.fp, result.fn), (0, 1, 1))

    def test_an_episode_that_opens_before_the_event_does_not_detect_it(self):
        result = self.match([event("EV-1", "Compute", "2026-09-09")], [episode("Compute", "2026-09-08")])
        self.assertEqual((result.tp, result.fp, result.fn), (0, 1, 1))

    def test_another_service_does_not_detect_the_event(self):
        result = self.match([event("EV-1", "Compute", "2026-09-09")], [episode("Storage", "2026-09-09")])
        self.assertEqual((result.tp, result.fp, result.fn), (0, 1, 1))

    def test_one_episode_covers_only_one_of_two_events(self):
        events = [event("EV-1", "Compute", "2026-09-09"), event("EV-2", "Compute", "2026-09-10")]
        result = self.match(events, [episode("Compute", "2026-09-10")])
        self.assertEqual((result.tp, result.fp, result.fn), (1, 0, 1))

    def test_the_earlier_event_wins_a_contested_episode_whatever_the_input_order(self):
        early, late = event("EV-1", "Compute", "2026-09-09"), event("EV-2", "Compute", "2026-09-10")
        for events in ([early, late], [late, early]):
            result = self.match(events, [episode("Compute", "2026-09-10")])
            self.assertEqual(sorted(result.delays), ["EV-1"], events)

    def test_an_episode_with_no_event_is_a_false_positive(self):
        result = self.match([], [episode("Storage", "2026-10-20")])
        self.assertEqual((result.tp, result.fp, result.fn), (0, 1, 0))

    def test_tolerance_zero_requires_the_same_day(self):
        result = self.match([event("EV-1", "Compute", "2026-09-09")], [episode("Compute", "2026-09-10")], tolerance=0)
        self.assertEqual((result.tp, result.fn), (0, 1))


class RatesFromTheCounts(unittest.TestCase):
    def report(self, events, episodes):
        return tool.build_report(events, episodes, tolerance=3, reference=date(2026, 10, 30), commit=None, run_at=None)

    def test_no_episodes_leaves_the_precision_not_measured_with_denominator_zero(self):
        precision = row(self.report([event("EV-1", "Compute", "2026-09-09")], []), "precision")
        self.assertEqual((precision["status"], precision.get("value"), precision.get("numerator"), precision["denominator"]),
                         ("not_measured", None, None, 0))

    def test_no_events_leaves_both_recalls_not_measured(self):
        report = self.report([], [episode("Compute", "2026-09-09")])
        self.assertEqual(row(report, "recall_all")["status"], "not_measured")
        self.assertEqual(row(report, "recall_designed")["status"], "not_measured")

    def test_zero_true_positives_is_a_measured_zero_precision(self):
        report = self.report([event("EV-1", "Compute", "2026-09-09")], [episode("Storage", "2026-09-09")])
        precision = row(report, "precision")
        self.assertEqual((precision["status"], precision["value"], precision["numerator"], precision["denominator"]),
                         ("measured", 0.0, 0, 1))

    def test_the_delay_is_not_measured_without_detections_and_not_zero(self):
        report = self.report([event("EV-1", "Compute", "2026-09-09")], [])
        self.assertEqual(row(report, "detection_delay_days")["status"], "not_measured")

    def test_the_mean_delay_averages_only_detected_events(self):
        events = [event("EV-1", "Compute", "2026-09-09"), event("EV-2", "Storage", "2026-09-10"), event("EV-3", "Tools", "2026-09-11")]
        report = self.report(events, [episode("Compute", "2026-09-09"), episode("Storage", "2026-09-13")])
        self.assertEqual(row(report, "detection_delay_days")["value"], 1.5)

    def test_a_miss_of_an_undetectable_event_lowers_only_the_all_recall(self):
        events = [event("EV-1", "Compute", "2026-09-09"), event("EV-2", "Backup", "2026-09-10", designed=False)]
        report = self.report(events, [episode("Compute", "2026-09-09")])
        self.assertEqual((row(report, "recall_all")["numerator"], row(report, "recall_all")["denominator"]), (1, 2))
        self.assertEqual((row(report, "recall_designed")["numerator"], row(report, "recall_designed")["denominator"]), (1, 1))

    def test_a_miss_of_a_detectable_event_lowers_both_recalls(self):
        events = [event("EV-1", "Compute", "2026-09-09"), event("EV-2", "Tools", "2026-10-08")]
        report = self.report(events, [episode("Compute", "2026-09-09")])
        self.assertEqual(row(report, "recall_all")["value"], 0.5)
        self.assertEqual(row(report, "recall_designed")["value"], 0.5)

    def test_a_detected_undetectable_event_is_not_counted_against_the_designed_recall(self):
        events = [event("EV-1", "Backup", "2026-09-10", designed=False)]
        report = self.report(events, [episode("Backup", "2026-09-10")])
        self.assertEqual(row(report, "recall_designed")["status"], "not_measured")
        self.assertEqual(row(report, "recall_all")["value"], 1.0)

    def test_every_event_has_its_own_detected_row(self):
        events = [event("EV-1", "Compute", "2026-09-09"), event("EV-2", "Tools", "2026-10-08")]
        report = self.report(events, [episode("Compute", "2026-09-09")])
        self.assertEqual(row(report, "event_detected", "EV-1")["value"], 1)
        self.assertEqual(row(report, "event_detected", "EV-2")["value"], 0)


class RealDetector(unittest.TestCase):
    def measure(self, reference):
        return tool.anomaly_report(date.fromisoformat(reference), commit=None, run_at=None)

    def test_reference_30_october_opens_five_of_seven_events(self):
        report, _ = self.measure("2026-10-30")
        counts = {name: row(report, name)["value"] for name in ("events", "episodes", "tp", "fp", "fn")}
        self.assertEqual(counts, {"events": 7, "episodes": 5, "tp": 5, "fp": 0, "fn": 2})
        self.assertEqual(row(report, "precision")["value"], 1.0)
        self.assertEqual((row(report, "recall_all")["numerator"], row(report, "recall_all")["denominator"]), (5, 7))
        self.assertEqual((row(report, "recall_designed")["numerator"], row(report, "recall_designed")["denominator"]), (5, 5))
        self.assertEqual(row(report, "detection_delay_days")["value"], 0.0)

    def test_the_two_missed_events_are_backup_and_networking(self):
        report, _ = self.measure("2026-10-30")
        missed = sorted(r["behavior"] for r in report["results"] if r["metric_id"] == "event_detected" and r["value"] == 0)
        self.assertEqual(missed, ["EV-03", "EV-04"])

    def test_reference_21_september_only_counts_the_events_already_started(self):
        report, _ = self.measure("2026-09-21")
        counts = {name: row(report, name)["value"] for name in ("events", "episodes", "tp", "fp", "fn")}
        self.assertEqual(counts, {"events": 5, "episodes": 3, "tp": 3, "fp": 0, "fn": 2})

    def test_an_event_on_the_last_evaluated_day_is_counted_and_detected(self):
        report, _ = self.measure("2026-09-17")
        self.assertEqual(row(report, "events")["value"], 5)
        self.assertEqual(row(report, "event_detected", "EV-05")["value"], 1)

    def test_an_event_the_day_after_the_last_evaluated_day_is_not_counted(self):
        report, _ = self.measure("2026-09-16")
        self.assertEqual(row(report, "events")["value"], 4)
        self.assertEqual([r for r in report["results"] if r["behavior"] == "EV-05"], [])

    def test_the_harness_opens_the_same_episodes_as_the_reference_file_of_the_demo(self):
        for reference, wanted in EXPECTED["episodes_by_reference"].items():
            opened = tool.run_detector(date.fromisoformat(reference))
            self.assertEqual(sorted((e.service, e.start_date.isoformat()) for e in opened),
                             sorted((e["service"], e["start_date"]) for e in wanted["episodes"]), reference)

    def test_a_reference_before_any_complete_day_is_rejected(self):
        with self.assertRaises(tool.IndicatorError):
            self.measure("2026-06-01")

    def test_the_report_passes_the_common_rows_contract(self):
        report, _ = self.measure("2026-10-30")
        run, results = dashboard.adapt_rows_v1(report)
        self.assertEqual(run["source"], "JUP-130")
        self.assertTrue(all(r["measure_type"] == "A" and r["judgment"] == "automatic" for r in results))
        self.assertTrue(all(r["grp"] == "anomaly_detection" for r in results))
        self.assertIs(run["synthetic"], True)

    def test_two_runs_with_the_same_inputs_are_identical_byte_for_byte(self):
        first = self.measure("2026-10-30")
        second = self.measure("2026-10-30")
        self.assertEqual(json.dumps(first[0], sort_keys=False), json.dumps(second[0], sort_keys=False))
        self.assertEqual(first[1], second[1])

    def test_the_table_declares_the_limits_and_the_command(self):
        _, table = self.measure("2026-10-30")
        for phrase in ("sintéticos", "7 eventos", "diseñó los datos", "validez estadística", "facturas reales",
                       "python tools/memory-indicators.py anomalies --reference 2026-10-30"):
            self.assertIn(phrase, table)

    def test_the_table_writes_decimals_with_a_comma(self):
        _, table = self.measure("2026-10-30")
        for text in ("100,0 % (5/5)", "71,4 % (5/7)", "0,0 días"):
            self.assertIn(text, table)
        self.assertNotRegex(table, r"\d\.\d %")

    def test_the_table_lists_every_event_with_its_outcome(self):
        _, table = self.measure("2026-10-30")
        for identifier in ("EV-01", "EV-02", "EV-03", "EV-04", "EV-05", "EV-06", "EV-07"):
            self.assertIn(identifier, table)
        self.assertIn("no detectable por diseño", table)


class Command(unittest.TestCase):
    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL_PATH), *args], capture_output=True, text=True,
                              encoding="utf-8", cwd=ROOT)

    def test_it_writes_the_report_and_the_table(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_tool("anomalies", "--reference", "2026-10-30", "--out", directory,
                                   "--run-at", "2026-10-21T12:00:00Z", "--commit", "a" * 40)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(directory) / "JUP-130-anomalies.rows.json").read_text("utf-8"))
            self.assertEqual(report["run"]["run_at"], "2026-10-21T12:00:00Z")
            self.assertEqual(report["run"]["commit"], "a" * 40)
            self.assertTrue((Path(directory) / "JUP-130-anomalies.md").is_file())

    def test_a_missing_reference_is_a_usage_error(self):
        result = self.run_tool("anomalies")
        self.assertEqual(result.returncode, 2)

    def test_an_invalid_date_is_a_usage_error_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_tool("anomalies", "--reference", "30-10-2026", "--out", directory)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_a_run_at_that_is_not_utc_iso_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_tool("anomalies", "--reference", "2026-10-30", "--out", directory, "--run-at", "ayer")
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
