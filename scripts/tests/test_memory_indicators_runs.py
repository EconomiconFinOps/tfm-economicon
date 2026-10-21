"""Las tres ejecuciones de JUP-130 comparten fuente y no se anotan entre sí como cambios de configuración."""
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

# Los campos con los que la vista `evaluation.config_changes` compara una ejecución con la anterior de su misma fuente.
COMPARED = ("suite_version", "suite_sha256", "generation_model", "prompt_sha256", "corpus_sha256")


def runs() -> dict[str, dict]:
    chat = {"request_id": "gen-1", "call_type": "acompletion", "status": "success", "spend": 0.5, "model": "m",
            "startTime": "2026-10-15T10:00:00Z", "metadata": {}}
    return {
        "anomalies": tool.anomaly_report(date(2026, 10, 30), commit=None, run_at="2026-10-21T10:00:00Z")[0]["run"],
        "data": tool.data_report(fetch=None, reference_date_from_api=None, reference=date(2026, 10, 30), commit=None,
                                 run_at="2026-10-21T10:01:00Z")[0]["run"],
        "ai-cost": tool.ai_cost_report([chat], date(2026, 10, 12), date(2026, 10, 21), None, 10, commit=None,
                                       run_at="2026-10-21T10:02:00Z")[0]["run"],
    }


class RunsOfTheSameSource(unittest.TestCase):
    def test_the_three_runs_share_the_source(self):
        self.assertEqual({run["source"] for run in runs().values()}, {"JUP-130"})

    def test_the_three_runs_declare_the_same_suite_and_version(self):
        self.assertEqual({(run["suite"], run["suite_version"]) for run in runs().values()}, {("jup130-indicators", "1")})

    def test_no_run_carries_a_field_the_view_compares_beyond_the_shared_version(self):
        for name, run in runs().items():
            for field in COMPARED[1:]:
                self.assertNotIn(field, run, f"{name}.{field}")

    def test_the_compared_fields_are_identical_across_the_three_runs(self):
        compared = {name: {f: run.get(f) for f in COMPARED} for name, run in runs().items()}
        self.assertEqual(len({tuple(sorted(v.items())) for v in compared.values()}), 1, compared)

    def test_each_run_keeps_its_own_identifier(self):
        ids = [run["run_id"] for run in runs().values()]
        self.assertEqual(len(set(ids)), 3)


if __name__ == "__main__":
    unittest.main()
