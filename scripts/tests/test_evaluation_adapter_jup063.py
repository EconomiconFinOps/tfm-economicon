"""Comparación pareada histórica: fidelidad, rechazo y proyección SQL sin servicios.

La consulta REAL del panel se ejecuta con SQLite (subconjunto SELECT/FILTER común).
Esto comprueba la conciliación de cifras, no el datasource PostgreSQL ni Grafana vivo.
El informe original publicado por JUP-063 es la fuente; no se ejecutan modelos.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "evaluation_jup063", os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools/evaluation-dashboard.py"
)
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)
REPORT = ROOT / "docs/evidence/JUP-063/glm-deepseek-20261016/comparison.json"
MANIFEST = ROOT / "docs/validation/evaluation-glm-deepseek-runs.json"
DASHBOARD = ROOT / "apps/monitoring/grafana/dashboards/assistant-evaluation.json"


def source():
    return json.loads(REPORT.read_text(encoding="utf-8"))


class PairedComparisonTests(unittest.TestCase):
    def dataset(self):
        return tool.build_dataset([MANIFEST], root=ROOT)

    def reject(self, field, value, fragment=None):
        report = source()
        target = report
        for key in field[:-1]:
            target = target[key]
        target[field[-1]] = value
        with self.assertRaises(tool.AdapterError) as caught:
            tool.adapt_jup063_paired(report, "paired-test")
        self.assertIn(fragment or ".".join(field), str(caught.exception))

    def test_real_counts_are_not_acceptance_cases(self):
        data = self.dataset()
        self.assertEqual(len(data["runs"]), 1)
        self.assertEqual(len(data["runs"][0]["results"]), 18)
        results = {(r["behavior"], r["metric_id"]): r for r in data["runs"][0]["results"]}
        for alias, counts in (("DeepSeekV4.1Flash", (77, 6, 1)), ("GLM5.2", (82, 2, 0))):
            for metric, n in zip(tool.PAIRED_VERDICTS, counts):
                row = results[alias, metric]
                self.assertEqual(row["value"], n)
                self.assertEqual(row["denominator"], 84)
                self.assertEqual(row["status"], "measured")
            self.assertEqual(results[alias, "sample_size"]["value"], 84)
        self.assertEqual({r["grp"] for r in data["runs"][0]["results"]}, {"paired_local_provisional"})
        self.assertFalse(any(r["metric_id"] in {"cases", "ACC-1"} for r in data["runs"][0]["results"]))
        for r in data["runs"][0]["results"]:
            self.assertEqual(r["judgment"], None if r["metric_id"] in tool.PAIRED_VERDICTS else "automatic")

    def test_provisional_attribution_is_not_automatic_or_human(self):
        run, rows = tool.adapt_jup063_paired(source(), "paired-test")
        provisional = [r for r in rows if r["metric_id"] in tool.PAIRED_VERDICTS]
        self.assertEqual(len(provisional), 6)
        self.assertFalse(any(r["judgment"] in {"automatic", "human"} for r in provisional))
        for key, value in (("grp", "accuracy"), ("metric_id", "ACC-1")):
            row = dict(provisional[0], **{key: value})
            with self.assertRaisesRegex(tool.AdapterError, "judgment"):
                tool.validate_rows(run, [row])
        technical = next(r for r in rows if r["metric_id"] == "sample_size")
        with self.assertRaisesRegex(tool.AdapterError, "judgment"):
            tool.validate_rows(run, [dict(technical, judgment=None)])

    def test_units_and_exact_source_values_are_preserved(self):
        run, rows = tool.adapt_jup063_paired(source(), "paired-test")
        tool.validate_rows(run, rows)
        for row in rows:
            model = source()["models"][row["behavior"]]
            metric = row["metric_id"]
            if metric.startswith("generation_seconds_"):
                self.assertEqual(row["value"], model[metric])
                self.assertEqual(row["unit"], "s")
            if metric == "reported_phase_cost_usd":
                self.assertEqual(row["value"], float(model[metric]))
                self.assertEqual(row["unit"], "usd")
                self.assertIsNone(row["denominator"])

    def test_unknown_fields_stay_null_and_no_text_is_projected(self):
        run, rows = tool.adapt_jup063_paired(source(), "paired-test")
        for key in ("run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
                    "embedding_provider", "embedding_alias", "generation_model", "prompt_sha256", "retrieval"):
            self.assertIsNone(run[key], key)
        report = source()
        report["prompt"] = "PRIVATE PROMPT NOT FOR GRAFANA"
        report["models"]["GLM5.2"]["answer"] = "PRIVATE ANSWER"
        actual = json.dumps(tool.adapt_jup063_paired(report, "paired-test"))
        self.assertNotIn("PRIVATE", actual)
        self.assertNotIn("requirements", actual)

    def test_adapter_is_pure(self):
        report = source()
        before = copy.deepcopy(report)
        tool.adapt_jup063_paired(report, "paired-test")
        self.assertEqual(report, before)

    def test_null_is_not_zero(self):
        report = source()
        model = report["models"]["GLM5.2"]
        model["reported_phase_cost_usd"] = None
        model["generation_seconds_p50"] = None
        run, rows = tool.adapt_jup063_paired(report, "paired-test")
        tool.validate_rows(run, rows)
        for metric in ("reported_phase_cost_usd", "generation_seconds_p50"):
            row = next(r for r in rows if r["behavior"] == "GLM5.2" and r["metric_id"] == metric)
            self.assertIsNone(row["value"])
            self.assertEqual(row["status"], "not_measured")

    def test_partial_cost_is_explicit_not_suppressed_or_totalized(self):
        report = source()
        report["models"]["GLM5.2"]["phases_with_unknown_cost"] = 2
        _, rows = tool.adapt_jup063_paired(report, "paired-test")
        r = {r["metric_id"]: r for r in rows if r["behavior"] == "GLM5.2"}
        self.assertEqual(r["unknown_cost_phases"]["value"], 2)
        self.assertEqual(r["reported_phase_cost_usd"]["value"], .3470654625)

    def test_reject_state_schema_and_acceptance_drift(self):
        self.reject(("state",), "CANONICAL_ACCEPTED", "state")
        self.reject(("models",), [], "models")
        self.reject(("models", "GLM5.2", "acceptance"), "APPROVED")
        self.reject(("models", "GLM5.2", "latency_scope"), "end-to-end")

    def test_reject_inconsistent_counts_and_unpaired_sizes(self):
        for value in (True, -1, 0, 84.5):
            with self.subTest(value=value):
                self.reject(("models", "GLM5.2", "responses"), value)
        self.reject(("models", "GLM5.2", "verdicts"), {"provisional_pass": 83})
        self.reject(("models", "GLM5.2", "verdicts"), {"pass": 84})
        self.reject(("models", "GLM5.2", "verdicts"), {"provisional_pass": True})
        report = source()
        report["models"]["GLM5.2"].update(responses=83, verdicts={"provisional_pass": 83})
        with self.assertRaisesRegex(tool.AdapterError, "models.responses"):
            tool.adapt_jup063_paired(report, "paired-test")

    def test_reject_cost_and_latency_nonfinite_or_wrong_units(self):
        for value in (True, .34, "NaN", "Infinity", "-1", "1 USD", "9" * 400):
            with self.subTest(value=value):
                self.reject(("models", "GLM5.2", "reported_phase_cost_usd"), value)
        for value in (True, "22", float("inf"), float("nan"), -1):
            with self.subTest(value=value):
                self.reject(("models", "GLM5.2", "generation_seconds_p95"), value)
        self.reject(("models", "GLM5.2", "generation_seconds_p95"), 1,
                    "models.GLM5.2.generation_seconds")

    def test_duplicate_manifest_is_rejected_without_repeated_rows(self):
        with self.assertRaises(tool.ManifestError):
            tool.build_dataset([MANIFEST, MANIFEST], root=ROOT)

    def test_rows_and_transactional_sql_are_deterministic(self):
        first, second = self.dataset(), self.dataset()
        self.assertEqual(first, second)
        sql = tool.build_sql(first)
        self.assertEqual(sql, tool.build_sql(second))
        self.assertIn("BEGIN;", sql)
        self.assertIn("COMMIT;", sql)
        self.assertIn("TRUNCATE", sql)
        self.assertIn("paired_local_provisional", sql)
        self.assertEqual(first["runs"][0]["run"]["report_sha256"], tool.report_digest(source()))

    def test_scoped_sql_has_no_ddl_roles_or_global_delete(self):
        data = self.dataset()
        sql = tool.build_comparison_sql(data)
        self.assertEqual(sql, tool.build_comparison_sql(self.dataset()))
        self.assertTrue(sql.startswith("BEGIN;"))
        self.assertTrue(sql.endswith("COMMIT;\n"))
        for forbidden in ("TRUNCATE", "CREATE", "ALTER", "DROP", "GRANT", "REVOKE"):
            self.assertNotIn(forbidden, sql)
        run = data["runs"][0]["run"]
        self.assertIn(run["run_id"], sql)
        self.assertIn(run["report_sha256"], sql)
        self.assertIn("DELETE FROM evaluation.runs WHERE run_id =", sql)
        with self.assertRaises(tool.SqlError):
            tool.build_comparison_sql(tool.build_dataset([tool.DEFAULT_MANIFEST, MANIFEST], root=ROOT))
        bad = copy.deepcopy(data)
        bad["runs"][0]["run"]["run_id"] = "foreign-run"
        with self.assertRaises(tool.SqlError):
            tool.build_comparison_sql(bad)

    def test_addition_preserves_historical_default_dataset(self):
        historical = tool.build_dataset([tool.DEFAULT_MANIFEST], root=ROOT)
        with_comparison = tool.build_dataset([tool.DEFAULT_MANIFEST, MANIFEST], root=ROOT)
        self.assertEqual(len(historical["runs"]), 6)
        self.assertEqual(len(with_comparison["runs"]), 7)
        self.assertEqual(historical["runs"], with_comparison["runs"][:6])

    def test_panel_actual_query_conciles_all_source_metrics(self):
        dashboard = json.loads(DASHBOARD.read_text(encoding="utf-8"))
        panel = next(p for p in dashboard["panels"] if p["id"] == 25)
        self.assertIn("provisional", panel["title"])
        self.assertIn("No demuestra:", panel["description"])
        self.assertIn("aceptación", panel["description"])
        data = self.dataset()
        with sqlite3.connect(":memory:") as db:
            db.execute("ATTACH DATABASE ':memory:' AS evaluation")
            db.execute("CREATE TABLE evaluation.runs(run_id TEXT PRIMARY KEY, source TEXT, format TEXT, is_real INTEGER, non_real_reasons TEXT)")
            db.execute("CREATE TABLE evaluation.results(run_id TEXT, behavior TEXT, grp TEXT, metric_id TEXT, status TEXT, value REAL)")
            for entry in data["runs"]:
                r = entry["run"]
                db.execute("INSERT INTO evaluation.runs VALUES (?, ?, ?, ?, ?)", (r["run_id"], r["source"], r["format"], r["is_real"], json.dumps(r["non_real_reasons"])))
            for r in data["runs"][0]["results"]:
                db.execute("INSERT INTO evaluation.results VALUES (?, ?, ?, ?, ?, ?)",
                           (data["runs"][0]["run"]["run_id"],) + tuple(r[k] for k in ("behavior", "grp", "metric_id", "status", "value")))
            db.create_function("array_to_string", 2, lambda value, sep: sep.join(json.loads(value)))
            db.row_factory = sqlite3.Row
            actual = [dict(r) for r in db.execute(panel["targets"][0]["rawSql"])]
        self.assertEqual(len(actual), 2)
        for row in actual:
            original = source()["models"][row["model"]]
            self.assertEqual(row["sample_size"], original["responses"])
            for metric in tool.PAIRED_VERDICTS:
                self.assertEqual(row[metric], original["verdicts"].get(metric, 0))
            for metric in ("generation_seconds_p50", "generation_seconds_p95", "generation_seconds_max"):
                self.assertEqual(row[metric], original[metric])
            self.assertEqual(row["reported_phase_cost_usd"], float(original["reported_phase_cost_usd"]))
            self.assertEqual(row["unknown_cost_phases"], 0)
            self.assertIn("sin aceptación", row["estado"])

    def test_cli_bad_report_is_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bad.json").write_text('{"state":"WRONG"}', encoding="utf-8")
            (root / "manifest.json").write_text(json.dumps({"manifest_version": 1, "runs": [
                {"path": "bad.json", "format": "jup-063-paired-v1", "milestone": False}]}), encoding="utf-8")
            output = root / "output.json"
            output.write_text("preserved", encoding="utf-8")
            done = subprocess.run([sys.executable, str(tool.__file__), "rows", "--no-versioned", "--root", str(root),
                                   "--manifest", str(root / "manifest.json"), "--output", str(output)],
                                  capture_output=True, text=True)
            self.assertEqual(done.returncode, 1)
            self.assertEqual(done.stdout, "")
            self.assertIn("state", done.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "preserved")


if __name__ == "__main__":
    unittest.main()
