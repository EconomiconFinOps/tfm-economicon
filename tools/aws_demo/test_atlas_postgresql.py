"""Atlas acceptance against an explicitly disposable, isolated PostgreSQL server."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


class AtlasArtifactTests(unittest.TestCase):
    def test_exact_package_and_canonical_sources(self):
        data = ROOT / 'apps/backend/app/aws_atlas_data'
        self.assertEqual(hashlib.sha256((data / 'evaluations.sql').read_bytes()).hexdigest(),
                         'b61d9ffcc04e02d8a3df9847a7b4ffe21397d44afc5dd1d7384b7c30981a6f09')
        manifest = json.loads((data / 'manifest.json').read_text())
        self.assertEqual((manifest['runs'], manifest['results']), (19, 1688))
        for entry in manifest['entries']:
            value = json.loads((ROOT / entry['report_path']).read_text(encoding='utf-8'))
            canonical = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
            self.assertEqual(hashlib.sha256(canonical).hexdigest(), entry['report_sha256'], entry['run_id'])


@unittest.skipUnless(os.environ.get('AWS_POSTGRES_TEST_URL'), 'dedicated PostgreSQL opt-in required')
class AtlasPostgreSQLTests(unittest.TestCase):
    def setUp(self):
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url
        url = make_url(os.environ['AWS_POSTGRES_TEST_URL'])
        self.assertEqual(url.drivername, 'postgresql+psycopg')
        self.assertIn(url.host, {'localhost', '127.0.0.1', '::1'})
        self.assertNotIn(url.port, {None, 5432, 26257})
        self.assertEqual(url.database, 'economicon_jup131_test')
        self.admin = create_engine(url, isolation_level='AUTOCOMMIT')
        self.database = 'jup131_atlas_' + uuid4().hex
        with self.admin.connect() as c:
            c.execute(text(f'CREATE DATABASE "{self.database}"'))
        self.engine = create_engine(url.set(database=self.database))
        sys.path.insert(0, str(ROOT / 'apps/backend'))
        from app.aws_atlas import import_evaluations, configure_reader
        self.load, self.reader = import_evaluations, configure_reader
        self.url = url

    def tearDown(self):
        from sqlalchemy import text
        if hasattr(self, 'engine'):
            self.engine.dispose()
        if hasattr(self, 'admin'):
            with self.admin.connect() as c:
                c.execute(text(f'DROP DATABASE "{self.database}" WITH (FORCE)'))
                c.execute(text('DROP ROLE IF EXISTS grafana_evaluation_reader'))
            self.admin.dispose()

    def counts(self):
        from sqlalchemy import text
        with self.engine.connect() as c:
            return tuple(c.execute(text('SELECT (SELECT count(*) FROM evaluation.runs),'
                                        '(SELECT count(*) FROM evaluation.results)')).one())

    def test_additive_idempotent_and_preserves_unrelated_history(self):
        from sqlalchemy import text
        self.load(self.engine)
        self.assertEqual(self.counts(), (19, 1688))
        with self.engine.begin() as c:
            c.execute(text("INSERT INTO evaluation.runs SELECT 'extra-run', source, run_at, commit_sha, suite, suite_version, suite_sha256, corpus_sha256, embedding_provider, embedding_alias, retrieval, generation_model, prompt_sha256, synthetic, generation_model_id, generation_provider, generation_quantization, gateway_config_sha256, is_real, non_real_reasons, comparability_key, format, milestone, report_path, report_sha256 FROM evaluation.runs LIMIT 1"))
            c.execute(text("INSERT INTO evaluation.results SELECT 'extra-run', measure_type, grp, metric_id, behavior, status, case_count, value, unit, numerator, denominator, ci_low, ci_high, judgment, selected FROM evaluation.results LIMIT 1"))
        self.load(self.engine)
        self.assertEqual(self.counts(), (20, 1689))
        self.load(self.engine)
        self.assertEqual(self.counts(), (20, 1689))

    def test_conflicting_identity_aborts_without_partial_import(self):
        from sqlalchemy import text
        self.load(self.engine)
        with self.engine.begin() as c:
            c.execute(text("UPDATE evaluation.runs SET report_sha256=repeat('0',64) WHERE run_id=(SELECT min(run_id) FROM evaluation.runs)"))
            c.execute(text("DELETE FROM evaluation.results WHERE run_id=(SELECT max(run_id) FROM evaluation.runs)"))
            c.execute(text("DELETE FROM evaluation.runs WHERE run_id=(SELECT max(run_id) FROM evaluation.runs)"))
        before = self.counts()
        with self.assertRaises(Exception):
            self.load(self.engine)
        self.assertEqual(self.counts(), before)

    def test_reader_can_query_but_cannot_write_or_create(self):
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import DBAPIError
        self.load(self.engine)
        self.reader(self.engine, 'a' * 64)
        self.reader(self.engine, 'a' * 64)
        reader = create_engine(self.url.set(database=self.database, username='grafana_evaluation_reader', password='a' * 64))
        try:
            with reader.connect() as c:
                self.assertEqual(c.execute(text('SELECT count(*) FROM evaluation.results')).scalar_one(), 1688)
                c.rollback()
                for query in ['DELETE FROM evaluation.results', 'CREATE TABLE evaluation.forbidden(id int)', 'CREATE TABLE public.forbidden(id int)', 'CREATE TEMP TABLE forbidden(id int)']:
                    with self.subTest(query=query), self.assertRaises(DBAPIError):
                        c.execute(text(query))
                    c.rollback()
        finally:
            reader.dispose()

    def test_existing_privileged_reader_is_rejected(self):
        from sqlalchemy import text
        self.load(self.engine)
        with self.admin.connect() as c:
            c.execute(text('CREATE ROLE grafana_evaluation_reader CREATEDB'))
        with self.assertRaises(Exception):
            self.reader(self.engine, 'a' * 64)

    def test_changed_artifact_is_rejected_before_database_changes(self):
        from sqlalchemy import text
        from app import aws_atlas
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / 'altered.sql'
            changed.write_text('CREATE TABLE unexpected(id int);')
            with patch.object(aws_atlas, 'SQL_PATH', changed), self.assertRaises(Exception):
                self.load(self.engine)
        with self.engine.connect() as c:
            self.assertIsNone(c.execute(text("SELECT to_regnamespace('evaluation')")).scalar_one())

    def test_metadata_database_survives_repeated_setup_and_is_separate(self):
        from sqlalchemy import create_engine, text
        from app.aws_atlas import configure_metadata
        metadata = None
        try:
            configure_metadata(self.engine, 'b' * 64)
            metadata = create_engine(self.url.set(database='grafana', username='economicon_grafana', password='b' * 64))
            with metadata.begin() as c:
                c.execute(text('CREATE TABLE settings(value text)'))
                c.execute(text("INSERT INTO settings VALUES ('retained')"))
            configure_metadata(self.engine, 'b' * 64)
            with metadata.connect() as c:
                self.assertEqual(c.execute(text('SELECT value FROM settings')).scalar_one(), 'retained')
            with self.engine.connect() as c:
                self.assertIsNone(c.execute(text("SELECT to_regclass('settings')")).scalar_one())
        finally:
            if metadata is not None:
                metadata.dispose()
            with self.admin.connect() as c:
                c.execute(text('DROP DATABASE IF EXISTS grafana WITH (FORCE)'))
                c.execute(text('DROP ROLE IF EXISTS economicon_grafana'))


if __name__ == '__main__':
    unittest.main()
