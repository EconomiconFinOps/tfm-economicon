"""Actualización de una base de evaluación existente a los campos de identidad del modelo (JUP-133).

El esquema usa `CREATE TABLE IF NOT EXISTS`: en una base creada antes de JUP-133 la tabla `evaluation.runs` ya existe sin
las cuatro columnas nuevas, y una carga que solo hiciera `CREATE TABLE IF NOT EXISTS` fallaría al insertarlas. Aquí se
reproduce esa base con la tabla anterior escrita a mano (21 columnas) y se comprueba, contra un PostgreSQL real, que la
carga nueva la actualiza, conserva los permisos de lectura y es idempotente. Se salta sola sin Docker.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_pg_helper  # noqa: E402

IDENTITY = ("generation_model_id", "generation_provider", "generation_quantization", "gateway_config_sha256")
# La tabla `evaluation.runs` tal como la creaba el esquema anterior a JUP-133 (sin las columnas de identidad).
OLD_RUNS = """
CREATE SCHEMA IF NOT EXISTS evaluation;
CREATE TABLE evaluation.runs (
  run_id text PRIMARY KEY, source text NOT NULL, run_at timestamptz, commit_sha text, suite text, suite_version text,
  suite_sha256 text, corpus_sha256 text, embedding_provider text, embedding_alias text, retrieval jsonb,
  generation_model text, prompt_sha256 text, synthetic boolean NOT NULL, is_real boolean NOT NULL,
  non_real_reasons text[] NOT NULL, comparability_key text NOT NULL, format text NOT NULL, milestone boolean NOT NULL,
  report_path text, report_sha256 text NOT NULL
);
"""

_server = None


def setUpModule() -> None:
    global _server
    _server = evaluation_pg_helper.PostgresServer()


def tearDownModule() -> None:
    if _server is not None:
        _server.stop()


class UpgradeTests(unittest.TestCase):
    def setUp(self) -> None:
        _server.psql("DROP SCHEMA IF EXISTS evaluation CASCADE;")
        result = _server.psql(OLD_RUNS)
        self.assertEqual(result.returncode, 0, result.stderr)
        tool = evaluation_pg_helper.load_tool()
        self.dataset = tool.build_dataset([tool.DEFAULT_MANIFEST])

    def columns(self) -> set[str]:
        rows = _server.query("SELECT column_name FROM information_schema.columns "
                             "WHERE table_schema='evaluation' AND table_name='runs'")
        return {row[0] for row in rows}

    def test_the_old_table_has_no_identity_columns(self) -> None:
        self.assertFalse(set(IDENTITY) & self.columns())

    def test_loading_into_an_old_database_adds_the_columns_and_the_data(self) -> None:
        _server.load_dataset(self.dataset)
        self.assertTrue(set(IDENTITY) <= self.columns())
        self.assertEqual(int(_server.scalar("SELECT count(*) FROM evaluation.runs")), len(self.dataset["runs"]))
        self.assertEqual(
            int(_server.scalar("SELECT count(*) FROM evaluation.runs WHERE generation_model_id IS NOT NULL")),
            sum(1 for item in self.dataset["runs"] if item["run"]["generation_model_id"] is not None))

    def test_a_second_load_is_idempotent(self) -> None:
        _server.load_dataset(self.dataset)
        first = _server.scalar("SELECT md5(string_agg(r::text, '|' ORDER BY run_id)) FROM evaluation.runs r")
        _server.load_dataset(self.dataset)
        second = _server.scalar("SELECT md5(string_agg(r::text, '|' ORDER BY run_id)) FROM evaluation.runs r")
        self.assertEqual(first, second)

    def test_the_views_work_after_the_upgrade(self) -> None:
        _server.load_dataset(self.dataset)
        self.assertEqual(_server.psql("SELECT count(*) FROM evaluation.config_changes").returncode, 0)
        self.assertEqual(_server.psql("SELECT count(*) FROM evaluation.comparable_runs").returncode, 0)

    def test_two_chat_runs_with_the_same_alias_and_different_model_do_not_share_a_series(self) -> None:
        _server.load_dataset(self.dataset)
        rows = _server.query("SELECT generation_model_id, comparability_key FROM evaluation.runs WHERE source='JUP-071'")
        by_model = {}
        for model, key in rows:
            by_model.setdefault(model, set()).add(key)
        self.assertEqual(len(rows), 5)
        self.assertEqual(len(by_model), 2)
        keys = list(by_model.values())
        self.assertFalse(keys[0] & keys[1], "modelos distintos no comparten una serie")


if __name__ == "__main__":
    unittest.main()
