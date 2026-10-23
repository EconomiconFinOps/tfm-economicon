"""Manifiesto completo: seis repeticiones, rows originales y SQL real de Grafana.

Complementa los escenarios históricos aislados. Usa PostgreSQL desechable y el
rol de lectura; no escribe en la demo ni solicita respuestas al modelo.
"""
import json
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_readability_support as R
from evaluation_fixture_support import (
    ROOT, INFRA_IDS, INFRA_PATHS, INFRA_ROW_COUNTS, HISTORICAL_MANIFEST,
    VERSIONED_RUNS, VERSIONED_RESULTS,
)


class FullManifestTests(unittest.TestCase):
    def test_legacy_manifest_is_explicit_and_live_manifest_keeps_all_six_runs(self):
        historical = json.loads(HISTORICAL_MANIFEST.read_text(encoding="utf-8"))["runs"]
        current = json.loads((ROOT / "docs/validation/evaluation-runs.json").read_text(encoding="utf-8"))["runs"]
        self.assertEqual(len(historical), 12)
        self.assertEqual(current, historical + current[12:])
        self.assertEqual([entry["path"] for entry in current[12:]], list(INFRA_PATHS))
        self.assertTrue(all(not entry["milestone"] for entry in current[12:]))

    def test_full_load_has_all_reviewed_rows(self):
        rows = R.ejecutar("SELECT (SELECT count(*) FROM evaluation.runs) AS runs, "
                          "(SELECT count(*) FROM evaluation.results) AS results", completo=True)["filas"]
        self.assertEqual(rows, [{"runs": VERSIONED_RUNS, "results": VERSIONED_RESULTS}])

    def test_each_infra_result_matches_its_original_rows_file_including_nulls_and_judgments(self):
        columns = ("measure_type", "grp", "metric_id", "behavior", "status", "count", "value", "unit",
                   "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected")
        sql_columns = ", ".join('case_count AS count' if col == 'count' else col for col in columns)
        for path, run_id, count in zip(INFRA_PATHS, INFRA_IDS, INFRA_ROW_COUNTS):
            with self.subTest(run_id=run_id):
                raw = json.loads((ROOT / path).read_text(encoding="utf-8"))
                self.assertEqual(raw["run"]["run_id"], run_id)
                expected = [{key: row.get(key, False if key == "selected" else None) for key in columns}
                            for row in raw["results"]]
                actual = R.ejecutar(f"SELECT {sql_columns} FROM evaluation.results "
                                    f"WHERE run_id = {R.literal(run_id)}", completo=True)["filas"]
                self.assertEqual(len(actual), count)
                self.assertCountEqual(actual, expected)

    def test_infra_identity_is_declared_and_never_upgraded_to_verified_or_milestone(self):
        ids = ",".join(R.literal(run_id) for run_id in INFRA_IDS)
        rows = R.ejecutar("SELECT run_id, generation_model_id, generation_provider, generation_quantization, "
                          f"is_real, non_real_reasons, milestone FROM evaluation.runs WHERE run_id IN ({ids})",
                          completo=True)["filas"]
        self.assertEqual({row["run_id"] for row in rows}, set(INFRA_IDS))
        for row in rows:
            with self.subTest(run_id=row["run_id"]):
                self.assertEqual(row["generation_model_id"], "openrouter/deepseek/deepseek-v4.1-flash")
                self.assertEqual(row["generation_provider"], "deepinfra")
                self.assertEqual(row["generation_quantization"], "fp8")
                self.assertFalse(row["is_real"])
                self.assertFalse(row["milestone"])
                self.assertEqual(row["non_real_reasons"], ["sin_modelo_verificado"])

    def test_visible_run_metadata_and_case_counts_match_the_new_original_reports(self):
        def panel_rows(panel_id):
            panel = next(p for p in R.paneles() if p["id"] == panel_id)
            return R.ejecutar(R.consulta_unica(panel), completo=True)["filas"]
        loaded = {row["run_id"]: row for row in panel_rows(3)}
        cases = {row["run_id"]: row for row in panel_rows(4)}
        self.assertEqual(len(loaded), VERSIONED_RUNS)
        self.assertEqual(len(cases), 6)
        for path, run_id in zip(INFRA_PATHS, INFRA_IDS):
            raw = json.loads((ROOT / path).read_text(encoding="utf-8"))
            with self.subTest(run_id=run_id):
                row = loaded[run_id]
                self.assertEqual(datetime.fromisoformat(row["run_at"]), datetime.fromisoformat(raw["run"]["run_at"]))
                self.assertEqual(row["suite_version"], raw["run"]["suite_version"])
                self.assertEqual(row["estado"], "no real: sin_modelo_verificado")
                self.assertEqual(row["generation_identity"], "openrouter/deepseek/deepseek-v4.1-flash / deepinfra / fp8")
                if raw["run"]["source"] == "JUP-070":
                    original = [r for r in raw["results"] if r["grp"] == "cases" and r["metric_id"] == "cases"]
                    self.assertEqual(len(original), 4)
                    for result in original:
                        self.assertEqual(cases[run_id][result["status"]], result["count"])
                        self.assertEqual(cases[run_id]["denominator"], result["denominator"])

    def test_robustness_panel_preserves_each_new_result_and_does_not_fill_missing_values(self):
        panel = next(p for p in R.paneles() if p["id"] == 11)
        rows = R.ejecutar(R.consulta_unica(panel), completo=True)["filas"]
        self.assertEqual(len(rows), 1076)
        self.assertEqual({row["run_id"] for row in rows},
                         set(INFRA_IDS[3:]) | {"JUP-071-a543144c9a55", "JUP-071-864a0d6dc666"})
        keys = ("metric_id", "behavior", "status", "value", "numerator", "denominator")
        for path, run_id in zip(INFRA_PATHS[3:], INFRA_IDS[3:]):
            original = json.loads((ROOT / path).read_text(encoding="utf-8"))["results"]
            actual = [row for row in rows if row["run_id"] == run_id]
            with self.subTest(run_id=run_id):
                self.assertEqual(len(actual), 268)
                self.assertCountEqual([tuple(row.get(key) for key in keys) for row in actual],
                                      [tuple(row.get(key) for key in keys) for row in original])
                for row in actual:
                    if row["status"] == "not_measured":
                        self.assertIsNone(row["value"])
                        self.assertIsNone(row["valor_texto"])

    def test_robustness_indicator_panel_selects_the_latest_infra_repetition(self):
        panel = next(p for p in R.paneles() if p["id"] == 30)
        rows = R.ejecutar(R.consulta_unica(panel), completo=True)["filas"]
        self.assertEqual(len(rows), 19)
        for row in rows:
            self.assertEqual(datetime.fromisoformat(row["run_at"]),
                             datetime.fromisoformat("2026-10-23T16:32:09Z"))
            self.assertEqual(row["estado"], "no real: sin_modelo_verificado")
        completed = next(row for row in rows if row["indicador"] == "Operaciones completadas")
        self.assertEqual(completed["valor_texto"], "96.6 %")
        self.assertEqual(completed["base"], "28 de 29")

    def test_all_versioned_postgres_panels_and_annotations_execute_with_full_data(self):
        checked = 0
        for panel in R.paneles():
            for target in panel.get("targets", []):
                if target.get("rawSql"):
                    with self.subTest(panel=panel["id"], target=target.get("refId")):
                        R.ejecutar(target["rawSql"], completo=True)
                        checked += 1
        annotations_checked = 0
        for annotation in R.dashboard().get("annotations", {}).get("list", []):
            sql = annotation.get("target", {}).get("rawSql")
            if sql:
                R.ejecutar(sql, completo=True)
                annotations_checked += 1
        self.assertEqual(annotations_checked, 1)
        self.assertEqual(checked, 18)


if __name__ == "__main__":
    unittest.main()
