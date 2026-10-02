from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "tools" / "retrieval-calibration.py"
SPEC = importlib.util.spec_from_file_location("economicon_retrieval_calibration", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
calibration = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = calibration
SPEC.loader.exec_module(calibration)

CHUNKER_PATH = ROOT / "apps" / "processor" / "app" / "embeddings" / "chunker.py"
CHUNKER_SPEC = importlib.util.spec_from_file_location("economicon_ingestion_chunker", CHUNKER_PATH)
assert CHUNKER_SPEC is not None and CHUNKER_SPEC.loader is not None
ingestion_chunker = importlib.util.module_from_spec(CHUNKER_SPEC)
CHUNKER_SPEC.loader.exec_module(ingestion_chunker)

DOC = (
    "# Guia\n\n## Alpha\n" + "alpha alpha alpha alpha alpha alpha.\n\n"
    "## Beta\n" + "beta beta beta beta beta beta.\n\n"
    "```text\n## Falso\n```\n\n"
    "## Gamma\n" + "gamma gamma gamma gamma gamma gamma.\n"
)
SECRET_SENTENCE = "frase-secreta-que-no-debe-salir"
KEYWORDS = ["alpha", "beta", "gamma"]


class KeywordProvider:
    """Counts keywords: distances are exact and easy to reason about."""

    name = "keywords"
    dimension = len(KEYWORDS)

    def __init__(self):
        self.calls = 0

    def embed(self, text: str) -> list[float]:
        self.calls += 1
        lowered = text.lower()
        vector = [float(lowered.count(word)) for word in KEYWORDS]
        return vector if any(vector) else [0.0, 0.0, 1e-9]


class ForbiddenProvider:
    name = "forbidden"
    dimension = 3

    def embed(self, text: str) -> list[float]:
        raise AssertionError("el proveedor no debia llamarse")


def make_repo(extra_doc: str = "") -> tuple[Path, dict]:
    root = Path(tempfile.mkdtemp(prefix="jup022-cal-"))
    (root / "docs").mkdir()
    text = DOC + extra_doc
    (root / "docs/a.md").write_text(text, encoding="utf-8")
    digest = calibration.digest(text)
    suite = {
        "suite_version": "1.0.0",
        "sources": {"a": {"path": "docs/a.md", "sha256": digest}},
        "cases": [
            {"id": "JUP-069-001", "category": "costs", "behavior": "answer", "question": "alpha alpha", "sources": ["a"]},
            {"id": "JUP-069-002", "category": "costs", "behavior": "answer", "question": "beta", "sources": ["a"]},
            {"id": "JUP-069-003", "category": "scope", "behavior": "clarify", "question": "gamma gamma", "sources": ["a"]},
            {"id": "JUP-069-004", "category": "scope", "behavior": "answer", "question": "tema ajeno", "sources": ["a"]},
        ],
    }
    labels = {
        "labels": [
            {"case": "JUP-069-001", "coverage": "direct", "expect": [{"source": "a", "heading": "Alpha"}]},
            {"case": "JUP-069-002", "coverage": "partial", "expect": [{"source": "a", "heading": "Beta"}]},
            {"case": "JUP-069-003", "coverage": "direct", "expect": [{"source": "a", "heading": "Gamma"}]},
            {"case": "JUP-069-004", "coverage": "none", "expect": [], "note": "hueco"},
        ]
    }
    (root / "suite.json").write_text(json.dumps(suite), encoding="utf-8")
    (root / "labels.json").write_text(json.dumps(labels), encoding="utf-8")
    return root, suite


def run(root: Path, provider=None, **overrides):
    options = dict(
        repo_root=root, suite_path="suite.json", labels_path="labels.json", provider=provider or KeywordProvider(),
        chunk_size=60, chunk_overlap=10, top_ks=[1, 2, 4], max_distances=[None, 0.5], max_calls=100,
        min_hit_ratio=0.9, validate_labels=None, now="2026-10-03T00:00:00+00:00",
    )
    options.update(overrides)
    return calibration.run(**options)


class ChunkingTests(unittest.TestCase):
    def test_uses_the_same_chunks_as_the_ingestion_pipeline(self):
        for size, overlap in ((60, 10), (500, 50), (37, 0)):
            spans = calibration.chunk_spans(DOC, size, overlap)
            expected = ingestion_chunker.TextChunker(size, overlap).split(DOC)
            self.assertEqual([chunk for chunk, _, _ in spans], expected)

    def test_real_corpus_chunks_match_the_ingestion_pipeline(self):
        text = (ROOT / "docs/assistant-corpus/business-rules/economicon-mvp-rules.md").read_text(encoding="utf-8")
        spans = calibration.chunk_spans(text, 500, 50)
        self.assertEqual([chunk for chunk, _, _ in spans], ingestion_chunker.TextChunker(500, 50).split(text))

    def test_each_chunk_belongs_to_the_section_that_covers_most_of_it(self):
        sections = calibration.section_spans(DOC)
        self.assertEqual([name for name, _, _ in sections], ["Guia", "Alpha", "Beta", "Gamma"])
        for chunk, start, end in calibration.chunk_spans(DOC, 60, 10):
            owner = calibration.primary_section(sections, start, end)
            self.assertIn(owner, {"Guia", "Alpha", "Beta", "Gamma"})
        spans = calibration.chunk_spans(DOC, 60, 10)
        self.assertEqual(calibration.primary_section(sections, spans[0][1], spans[0][2]), "Alpha")
        self.assertEqual(calibration.primary_section(sections, spans[1][1], spans[1][2]), "Beta")

    def test_a_tie_goes_to_the_earlier_section(self):
        sections = [("Uno", 0, 10), ("Dos", 10, 20)]
        self.assertEqual(calibration.primary_section(sections, 5, 15), "Uno")

    def test_heading_like_lines_inside_code_fences_are_not_sections(self):
        self.assertNotIn("Falso", [name for name, _, _ in calibration.section_spans(DOC)])


class DistanceTests(unittest.TestCase):
    def test_cosine_distance(self):
        self.assertAlmostEqual(calibration.cosine_distance([1, 0], [1, 0]), 0.0)
        self.assertAlmostEqual(calibration.cosine_distance([1, 0], [0, 1]), 1.0)
        self.assertAlmostEqual(calibration.cosine_distance([1, 0], [-1, 0]), 2.0)

    def test_rejects_vectors_of_different_length_or_zero_norm(self):
        with self.assertRaises(ValueError):
            calibration.cosine_distance([1, 0], [1, 0, 0])
        with self.assertRaises(ValueError):
            calibration.cosine_distance([0, 0], [1, 0])


class RetrievalTests(unittest.TestCase):
    ITEMS = [("b", 0.2, 5), ("a", 0.2, 3), ("c", 0.9, 1), ("d", 0.4, 2)]

    def test_orders_by_distance_then_identifier_and_limits_top_k(self):
        ranked = calibration.retrieve([(i, d, n) for i, d, n in self.ITEMS], top_k=3, max_distance=None)
        self.assertEqual([item[2] for item in ranked], [3, 5, 2])

    def test_maximum_distance_filters_and_can_leave_nothing(self):
        self.assertEqual([item[2] for item in calibration.retrieve(self.ITEMS, top_k=4, max_distance=0.4)], [3, 5, 2])
        self.assertEqual(calibration.retrieve(self.ITEMS, top_k=4, max_distance=0.1), [])


class RunTests(unittest.TestCase):
    def test_measures_hits_by_document_and_by_section_separating_non_answer_cases(self):
        root, _ = make_repo()
        result = run(root)
        point = next(p for p in result["points"] if p["top_k"] == 1 and p["max_distance"] is None)
        self.assertEqual(point["answer"]["cases"], 3)
        self.assertEqual(point["non_answer"]["cases"], 1)
        self.assertEqual(point["answer"]["section_cases"], 2)
        self.assertEqual(point["answer"]["section_hit_rate"], 1.0)
        self.assertEqual(point["non_answer"]["document_hit_rate"], 1.0)

    def test_gap_cases_are_listed_and_excluded_from_the_section_rate(self):
        root, _ = make_repo()
        result = run(root)
        self.assertEqual(result["gaps"], ["JUP-069-004"])
        point = result["points"][0]
        self.assertEqual(point["answer"]["section_cases"], 2)

    def test_a_threshold_can_empty_answers_and_the_report_shows_it(self):
        root, _ = make_repo()
        result = run(root, max_distances=[None, 0.0001])
        strict = next(p for p in result["points"] if p["max_distance"] == 0.0001 and p["top_k"] == 4)
        self.assertGreater(strict["answer"]["empty_rate"], 0.0)
        self.assertLess(strict["answer"]["section_hit_rate"], 1.0)

    def test_selection_rule_ignores_non_answer_cases(self):
        root, _ = make_repo()
        first = run(root)["selection"]["candidates"]
        suite = json.loads((root / "suite.json").read_text(encoding="utf-8"))
        suite["cases"][2]["question"] = "beta beta"
        (root / "suite.json").write_text(json.dumps(suite), encoding="utf-8")
        second = run(root)["selection"]["candidates"]
        self.assertEqual(first, second)

    def test_does_not_open_network_or_database_connections(self):
        root, _ = make_repo()
        with mock.patch.object(socket, "socket", side_effect=AssertionError("conexion abierta")):
            run(root)
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        for forbidden in ("sqlalchemy", "psycopg", "create_engine"):
            self.assertNotIn(forbidden, source)

    def test_stops_before_the_first_call_when_the_budget_is_exceeded(self):
        root, _ = make_repo()
        with self.assertRaisesRegex(calibration.CalibrationError, r"llamadas previstas \(\d+\).*maximo permitido \(2\)"):
            run(root, provider=ForbiddenProvider(), max_calls=2)

    def test_validates_the_labels_before_any_provider_call(self):
        root, _ = make_repo()
        with self.assertRaises(calibration.CalibrationError):
            run(root, provider=ForbiddenProvider(), validate_labels=lambda: ["etiqueta invalida"])

    def test_outputs_have_the_required_fields_and_no_fragment_text(self):
        root, _ = make_repo(extra_doc="\n" + SECRET_SENTENCE + "\n")
        suite = json.loads((root / "suite.json").read_text(encoding="utf-8"))
        result = run(root)
        for field in ("provider", "corpus", "bank", "chunking", "sweep", "points", "cases", "gaps", "selection", "limits", "generated_at"):
            self.assertIn(field, result)
        for field in ("name", "dimension"):
            self.assertIn(field, result["provider"])
        self.assertEqual(result["bank"]["suite_version"], suite["suite_version"])
        self.assertEqual(result["chunking"], {"size": 60, "overlap": 10, "chunks": result["chunking"]["chunks"]})
        self.assertIn("sha256", result["corpus"]["a"])
        report = calibration.render_report(result)
        for text in (json.dumps(result, ensure_ascii=False), report):
            self.assertNotIn(SECRET_SENTENCE, text)
        self.assertIn("pocos documentos", report.lower())
        self.assertIn("JUP-069-004", report)
        self.assertIn(result["selection"]["rule"], report)

    def test_defaults_come_only_from_a_reported_sweep_point(self):
        root, _ = make_repo()
        result = run(root)
        reported = {(p["top_k"], p["max_distance"]) for p in result["points"]}
        for candidate in result["selection"]["candidates"]:
            self.assertIn((candidate["top_k"], candidate["max_distance"]), reported)

    def test_real_corpus_and_bank_run_with_the_simulated_provider(self):
        provider = calibration.BagOfWordsProvider(dimension=128)
        result = calibration.run(
            repo_root=ROOT, suite_path="docs/validation/JUP-069-questions.json",
            labels_path="docs/validation/JUP-022-retrieval-labels.json", provider=provider,
            chunk_size=500, chunk_overlap=50, top_ks=[1, 4], max_distances=[None], max_calls=1000,
            min_hit_ratio=0.9, validate_labels=None, now="2026-10-03T00:00:00+00:00",
        )
        self.assertEqual(len(result["cases"]), 28)
        self.assertEqual(result["gaps"], ["JUP-069-024", "JUP-069-026"])
        for point in result["points"]:
            self.assertTrue(0.0 <= point["answer"]["document_hit_rate"] <= 1.0)


class CommandLineTests(unittest.TestCase):
    def invoke(self, *args, env=None):
        environment = {key: value for key, value in os.environ.items() if not key.startswith("LITELLM")}
        environment.update(env or {})
        return subprocess.run([sys.executable, str(SCRIPT_PATH), *args], capture_output=True, text=True, env=environment, timeout=120)

    def test_real_provider_without_a_key_stops_before_any_call_and_names_the_setting(self):
        result = self.invoke("--provider", "litellm")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("LITELLM_API_KEY", result.stderr)

    def test_real_provider_with_a_key_prints_no_secret(self):
        result = self.invoke("--provider", "litellm", env={"LITELLM_API_KEY": "SENTINEL-clave-secreta", "LITELLM_BASE_URL": ""})
        self.assertNotIn("SENTINEL-clave-secreta", result.stdout + result.stderr)
        self.assertNotEqual(result.returncode, 0)

    def test_unknown_provider_is_rejected(self):
        self.assertNotEqual(self.invoke("--provider", "otro").returncode, 0)

    def test_simulated_dry_run_writes_json_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output, report = Path(directory) / "r.json", Path(directory) / "r.md"
            result = self.invoke("--provider", "simulated", "--output", str(output), "--report", str(report))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["provider"]["name"], "simulated")
            self.assertTrue(report.read_text(encoding="utf-8").startswith("# "))


@unittest.skipUnless(os.environ.get("JUP086_VECTOR_TEST_URL"), "JUP086_VECTOR_TEST_URL absent: disposable real pgvector not exercised")
class PgvectorParityTests(unittest.TestCase):
    def test_distance_equals_the_one_reported_by_pgvector(self):
        import psycopg  # noqa: PLC0415 - optional, only with a disposable database

        url = os.environ["JUP086_VECTOR_TEST_URL"].replace("postgresql+psycopg://", "postgresql://")
        left, right = [0.1, 0.7, -0.3, 0.2], [0.4, -0.1, 0.5, 0.9]
        with psycopg.connect(url) as connection:
            stored = connection.execute("SELECT %s::vector <=> %s::vector", (str(left), str(right))).fetchone()[0]
        self.assertAlmostEqual(calibration.cosine_distance(left, right), float(stored), places=6)


if __name__ == "__main__":
    unittest.main()
