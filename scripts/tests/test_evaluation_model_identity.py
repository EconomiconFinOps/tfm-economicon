"""Identidad del modelo de generación en las ejecuciones del dashboard de evaluación (JUP-133, grupo 2).

Contrato que se valida (`openspec/changes/jup-133-reevaluacion-metricas-modelo/specs/assistant-evaluation-dashboard`):

* Cuatro campos opcionales en `run` (`IDENTITY_KEYS`): `generation_model_id`, `generation_provider`,
  `generation_quantization` y `gateway_config_sha256`. Nulos por defecto; un valor no válido falla nombrando el campo.
* `comparability_key` los añade solo si alguno no es nulo: sin identidad, la clave es la de antes de este cambio.
* La entrada del manifiesto admite `model_identity`: rellena solo lo que el informe no trae, no cambia la huella del
  informe y un conflicto con el informe, una clave desconocida o un valor no válido hacen fallar la carga.
* La vista `config_changes` nombra qué cambió y distingue «una de las dos no registra la identidad».
* Ninguna ejecución de campaña del chat posterior a este cambio entra en el manifiesto versionado sin identidad.

La clave sin identidad se calcula aquí a mano con la fórmula anterior, no con la herramienta, para que una
regresión del cálculo no se compare consigo misma.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_identity", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

IDENTITY = ("generation_model_id", "generation_provider", "generation_quantization", "gateway_config_sha256")
FULL_IDENTITY = {
    "generation_model_id": "deepseek/deepseek-v4.1-flash",
    "generation_provider": "deepinfra",
    "generation_quantization": "fp8",
    "gateway_config_sha256": "ab" * 32,
}
# Fecha a partir de la cual una campaña del chat en el manifiesto versionado debe traer identidad (este cambio).
IDENTITY_REQUIRED_FROM = "2026-10-21T21:00:00Z"


def legacy_key(run: dict, reasons: tuple = ()) -> str:
    """Clave de comparabilidad anterior a JUP-133, escrita a mano."""
    fields = ("source", "suite_version", "suite_sha256", "corpus_sha256", "embedding_provider", "embedding_alias",
              "retrieval", "generation_model", "prompt_sha256")
    payload = [run[field] for field in fields] + [list(reasons)]
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def base_run(**changes) -> dict:
    run = dict.fromkeys(tool.RUN_KEYS)
    run.update(run_id="r1", source="JUP-071", run_at="2026-10-22T10:00:00Z", suite_version="1.0.0",
               suite_sha256="1f" * 32, embedding_provider="litellm", embedding_alias="economicon-embedding",
               generation_model="economicon-chat", synthetic=False)
    run.update(changes)
    return run


def rows_document(**run_extra) -> dict:
    run = {"run_id": "r1", "source": "JUP-071", "run_at": "2026-10-22T10:00:00Z", "generation_model": "economicon-chat"}
    run.update(run_extra)
    return {"contract_version": 1, "run": run, "results": [
        {"measure_type": "B", "grp": "x", "metric_id": "queries", "behavior": "all", "status": "measured",
         "value": 1, "unit": "recuento"}]}


class FileTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name).resolve()

    def write(self, name: str, data: object) -> Path:
        path = self.dir / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def manifest(self, report: Path, **entry_extra) -> Path:
        entry = {"path": str(report), "format": "rows-v1", "milestone": False}
        entry.update(entry_extra)
        return self.write("manifest.json", {"manifest_version": 1, "runs": [entry]})

    def normalize(self, report_doc: dict, **entry_extra) -> dict:
        report = self.write("report.json", report_doc)
        entry = tool.read_manifest(self.manifest(report, **entry_extra), root=self.dir)[0]
        return tool.normalize_entry(entry, root=self.dir)


class ContractFieldsTests(unittest.TestCase):
    def test_identity_fields_close_the_run_keys_after_synthetic(self) -> None:
        self.assertEqual(tool.IDENTITY_KEYS, IDENTITY)
        self.assertEqual(tool.RUN_KEYS[-5:], ("synthetic",) + IDENTITY)

    def test_columns_are_declared_in_the_database_schema(self) -> None:
        for key in IDENTITY:
            self.assertIn(f"  {key} text", tool.SCHEMA_DDL)
            self.assertIn(key, tool.RUN_COLUMNS)

    def test_valid_identity_passes_validation(self) -> None:
        tool.validate_rows(base_run(**FULL_IDENTITY), [])

    def test_missing_identity_is_valid_and_null(self) -> None:
        run, _ = tool.adapt_rows_v1(rows_document())
        for key in IDENTITY:
            self.assertIsNone(run[key])

    def test_rows_v1_with_identity_keeps_it(self) -> None:
        run, _ = tool.adapt_rows_v1(rows_document(**FULL_IDENTITY))
        for key, value in FULL_IDENTITY.items():
            self.assertEqual(run[key], value)

    def test_invalid_values_name_the_field(self) -> None:
        bad = {
            "generation_model_id": ["", "con espacios", "a" * 81, 3, True],
            "generation_provider": ["", "a b", "a" * 81, 3],
            "generation_quantization": ["", "a" * 81, 8, False, "fp 8"],
            "gateway_config_sha256": ["", "AB" * 32, "ab" * 31, "ab" * 33, "g" * 64, "ab" * 32 + "\n", 5],
        }
        for key, values in bad.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    with self.assertRaisesRegex(tool.AdapterError, f"run\\.{key}"):
                        tool.validate_rows(base_run(**{key: value}), [])


class ComparabilityTests(unittest.TestCase):
    def key(self, **changes) -> str:
        return tool.comparability_key(base_run(**changes), ())

    def test_run_without_identity_keeps_its_previous_key(self) -> None:
        run = base_run()
        self.assertEqual(tool.comparability_key(run, ()), legacy_key(run))
        self.assertEqual(tool.comparability_key(run, ("sintetica",)), legacy_key(run, ("sintetica",)))

    def test_same_alias_with_different_model_are_not_comparable(self) -> None:
        a = self.key(**FULL_IDENTITY)
        b = self.key(**{**FULL_IDENTITY, "generation_model_id": "z-ai/glm-5.2"})
        self.assertNotEqual(a, b)

    def test_each_identity_field_splits_the_series(self) -> None:
        reference = self.key(**FULL_IDENTITY)
        changed = {"generation_model_id": "otro/modelo", "generation_provider": "coreweave",
                   "generation_quantization": "fp4", "gateway_config_sha256": "cd" * 32}
        for field, value in changed.items():
            with self.subTest(field=field):
                self.assertNotEqual(reference, self.key(**{**FULL_IDENTITY, field: value}))

    def test_registered_identity_is_not_comparable_with_unregistered(self) -> None:
        self.assertNotEqual(self.key(**FULL_IDENTITY), self.key())

    def test_partial_identity_is_not_the_same_as_none_or_full(self) -> None:
        partial = self.key(generation_model_id="deepseek/deepseek-v4.1-flash")
        self.assertNotEqual(partial, self.key())
        self.assertNotEqual(partial, self.key(**FULL_IDENTITY))

    def test_identical_identity_gives_identical_key(self) -> None:
        self.assertEqual(self.key(**FULL_IDENTITY), self.key(**copy.deepcopy(FULL_IDENTITY)))

    def test_values_swapped_between_fields_do_not_collide(self) -> None:
        a = self.key(generation_model_id="x", generation_provider="y")
        b = self.key(generation_model_id="y", generation_provider="x")
        self.assertNotEqual(a, b)

    def test_null_is_not_the_string_null(self) -> None:
        self.assertNotEqual(self.key(generation_provider=None, generation_model_id="m"),
                            self.key(generation_provider="null", generation_model_id="m"))


class ManifestAnnotationTests(FileTestCase):
    def test_annotation_fills_missing_fields(self) -> None:
        item = self.normalize(rows_document(), model_identity=FULL_IDENTITY)
        for key, value in FULL_IDENTITY.items():
            self.assertEqual(item["run"][key], value)

    def test_annotation_does_not_change_the_report_fingerprint(self) -> None:
        plain = self.normalize(rows_document())
        annotated = self.normalize(rows_document(), model_identity=FULL_IDENTITY)
        self.assertEqual(plain["run"]["report_sha256"], annotated["run"]["report_sha256"])

    def test_annotation_changes_the_comparability_key(self) -> None:
        plain = self.normalize(rows_document())
        annotated = self.normalize(rows_document(), model_identity=FULL_IDENTITY)
        self.assertNotEqual(plain["run"]["comparability_key"], annotated["run"]["comparability_key"])

    def test_partial_annotation_leaves_the_rest_null(self) -> None:
        item = self.normalize(rows_document(), model_identity={"generation_model_id": "openrouter/z-ai/glm-5.2"})
        self.assertEqual(item["run"]["generation_model_id"], "openrouter/z-ai/glm-5.2")
        for key in IDENTITY[1:]:
            self.assertIsNone(item["run"][key])

    def test_annotation_equal_to_the_report_is_accepted(self) -> None:
        item = self.normalize(rows_document(generation_provider="deepinfra"),
                              model_identity={"generation_provider": "deepinfra"})
        self.assertEqual(item["run"]["generation_provider"], "deepinfra")

    def test_report_value_is_not_overwritten_and_conflict_names_both_values(self) -> None:
        with self.assertRaises(tool.AdapterError) as caught:
            self.normalize(rows_document(generation_provider="deepinfra"),
                           model_identity={"generation_provider": "coreweave"})
        message = str(caught.exception)
        self.assertIn("generation_provider", message)
        self.assertIn("deepinfra", message)
        self.assertIn("coreweave", message)

    def test_unknown_annotation_key_fails_naming_the_key(self) -> None:
        with self.assertRaisesRegex(tool.ManifestError, "generation_model"):
            report = self.write("report.json", rows_document())
            tool.read_manifest(self.manifest(report, model_identity={"generation_model": "x"}), root=self.dir)

    def test_annotation_must_be_an_object(self) -> None:
        for value in (None, [], "fp8", 3):
            with self.subTest(value=value):
                report = self.write("report.json", rows_document())
                with self.assertRaises(tool.ManifestError):
                    tool.read_manifest(self.manifest(report, model_identity=value), root=self.dir)

    def test_invalid_annotation_value_fails_naming_the_field(self) -> None:
        for key, value in (("generation_quantization", ""), ("gateway_config_sha256", "AB" * 32),
                           ("generation_model_id", "a" * 81)):
            with self.subTest(key=key):
                with self.assertRaisesRegex(tool.AdapterError, key):
                    self.normalize(rows_document(), model_identity={key: value})

    def test_entry_without_annotation_exposes_none(self) -> None:
        report = self.write("report.json", rows_document())
        entry = tool.read_manifest(self.manifest(report), root=self.dir)[0]
        self.assertIsNone(entry["model_identity"])

    def test_build_dataset_is_atomic_when_one_annotation_conflicts(self) -> None:
        report = self.write("report.json", rows_document(generation_provider="deepinfra"))
        manifest = self.manifest(report, model_identity={"generation_provider": "coreweave"})
        with self.assertRaises(tool.AdapterError):
            tool.build_dataset([manifest], root=self.dir)


class ViewTests(unittest.TestCase):
    def test_config_changes_lag_every_identity_field(self) -> None:
        for key in IDENTITY:
            self.assertIn(f"lag({key}) OVER w AS previous_{key}", tool.VIEWS_DDL)

    def test_config_changes_names_each_change(self) -> None:
        for label in ("identificador de modelo", "proveedor del modelo", "cuantizacion", "configuracion del gateway",
                      "identidad del modelo no registrada en una de las dos"):
            self.assertIn(f"'{label}'", tool.VIEWS_DDL)

    def test_existing_labels_keep_their_order(self) -> None:
        sql = tool.VIEWS_DDL
        order = [sql.index(f"'{label}'::text") for label in ("bateria", "modelo", "prompt", "corpus")]
        self.assertEqual(order, sorted(order))


DASHBOARD = ROOT / "apps" / "monitoring" / "grafana" / "dashboards" / "assistant-evaluation.json"
IDENTITY_TITLE = "Modelo servido (modelo / proveedor / cuantización)"


def dashboard_panels(panels):
    for panel in panels:
        yield panel
        yield from dashboard_panels(panel.get("panels", []))


class DashboardColumnTests(unittest.TestCase):
    def setUp(self) -> None:
        document = json.loads(DASHBOARD.read_text(encoding="utf-8"))
        self.tables = [(panel, target["rawSql"]) for panel in dashboard_panels(document["panels"])
                       for target in panel.get("targets", []) if "AS generation_model," in target.get("rawSql", "")]

    def test_there_are_tables_that_show_the_model_alias(self) -> None:
        self.assertGreaterEqual(len(self.tables), 11)

    def test_every_table_with_the_alias_also_shows_the_served_model(self) -> None:
        for panel, sql in self.tables:
            with self.subTest(panel=panel["title"]):
                self.assertIn("AS generation_identity", sql)
                for column in ("r.generation_model_id", "r.generation_provider", "r.generation_quantization"):
                    self.assertIn(column, sql)

    def test_unregistered_identity_reads_no_registrado_and_never_hides_a_null(self) -> None:
        for panel, sql in self.tables:
            with self.subTest(panel=panel["title"]):
                self.assertIn("THEN 'no registrado'", sql)
                self.assertNotIn("NULLIF", sql.upper())

    def test_the_column_has_its_title_next_to_the_alias_override(self) -> None:
        for panel, _ in self.tables:
            with self.subTest(panel=panel["title"]):
                overrides = panel["fieldConfig"]["overrides"]
                names = [o["matcher"]["options"] for o in overrides]
                self.assertEqual(names.index("generation_identity"), names.index("generation_model") + 1)
                override = overrides[names.index("generation_identity")]
                properties = {p["id"]: p["value"] for p in override["properties"]}
                alias = {p["id"]: p["value"] for p in overrides[names.index("generation_model")]["properties"]}
                if "custom.hidden" in alias:
                    self.assertTrue(properties["custom.hidden"])
                else:
                    self.assertEqual(properties["displayName"], IDENTITY_TITLE)


class VersionedManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dataset = tool.build_dataset([tool.DEFAULT_MANIFEST])
        self.runs = {item["run"]["run_id"]: item["run"] for item in self.dataset["runs"]}

    def test_historical_glm_runs_are_annotated_with_what_the_evidence_proves(self) -> None:
        for run_id in ("JUP-071-a543144c9a55", "jup130-ai-cost-2026-10-09-to-2026-10-21"):
            run = self.runs[run_id]
            self.assertEqual(run["generation_model_id"], "openrouter/z-ai/glm-5.2", run_id)
            self.assertIsNone(run["generation_provider"], run_id)
            self.assertIsNone(run["generation_quantization"], run_id)

    def test_runs_without_a_proven_model_stay_unregistered(self) -> None:
        for run_id, run in self.runs.items():
            if run["source"] in ("JUP-070", "JUP-078", "JUP-022", "JUP-068", "JUP-130-anomalies", "JUP-130-data"):
                for key in IDENTITY:
                    self.assertIsNone(run[key], f"{run_id}.{key}")

    def test_chat_campaigns_after_this_change_must_declare_the_model(self) -> None:
        for run_id, run in self.runs.items():
            if run["source"] in tool.CHAT_CAMPAIGN_SOURCES and (run["run_at"] or "") >= IDENTITY_REQUIRED_FROM:
                self.assertIsNotNone(run["generation_model_id"], f"{run_id} no registra el modelo")

    def test_annotated_report_fingerprints_are_unchanged(self) -> None:
        manifest = json.loads(tool.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        for entry in manifest["runs"]:
            if "model_identity" not in entry:
                continue
            document = json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
            run = next(r for r in self.runs.values() if r["report_path"] == entry["path"])
            self.assertEqual(run["report_sha256"], tool.report_digest(document))


if __name__ == "__main__":
    unittest.main()
