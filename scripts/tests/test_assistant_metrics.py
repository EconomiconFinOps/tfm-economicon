from __future__ import annotations

import copy
import os
import re
import importlib.util
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "tools" / "assistant-metrics.py"
SPEC = importlib.util.spec_from_file_location("economicon_assistant_metrics", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
metrics = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = metrics
SPEC.loader.exec_module(metrics)

BANK = json.loads((ROOT / "docs/validation/JUP-069-questions.json").read_text(encoding="utf8"))
LABELS = json.loads((ROOT / "docs/validation/JUP-022-retrieval-labels.json").read_text(encoding="utf8"))
CATALOGUE = metrics.load_catalogue()
PINNED_DEFINITIONS = ("1.0.0", "5c5fc0b5e962327e46edbf7c5487ba6ec283bf800e7a7c4a96679161e53fdedd")
CASES = {case["id"]: case for case in BANK["cases"]}
LABEL_BY_CASE = {label["case"]: label for label in LABELS["labels"]}
SOURCE_CASE = {"answer": [], "clarify": [], "abstain": []}
for case in BANK["cases"]:
    SOURCE_CASE[case["behavior"]].append(case["id"])
CRITICAL = [case["id"] for case in BANK["cases"] if case["expected"].get("numbers")]
ANSWERS_DIRECT = [case_id for case_id in SOURCE_CASE["answer"] if LABEL_BY_CASE[case_id]["coverage"] in ("direct", "partial")]


def blank_case(case_id: str) -> dict:
    return {
        "case": case_id, "outcome": "not_run", "checks": [], "retrieved": [], "citations": [], "figures": [],
        "latency_ms": {}, "failure_category": None, "failure_stage": None, "structured_ok": None,
        "evidence_refs": {"total": 0, "dangling": 0},
    }


def base_results() -> dict:
    return {
        "results_version": 1,
        "catalogue_version": CATALOGUE["catalogue_version"],
        "synthetic": True,
        "run": {
            "commit": "0123456789abcdef", "date": "2026-10-05",
            "bank": {"suite_version": BANK["suite_version"], "suite_sha256": metrics.suite_digest(BANK)},
            "corpus": {"sha256": "a" * 64, "documents": 3, "chunks": 120},
            "provider": "litellm", "alias": "economicon-embedding",
            "retrieval": {"top_k": 4, "max_distance": 0.6, "chunk_size": 500, "chunk_overlap": 50},
            "generation": {"model_alias": "economicon-chat", "temperature": 0},
            "availability": {"requests": 200, "server_errors": 3},
        },
        "cases": [blank_case(case_id) for case_id in CASES],
    }


def case_of(results: dict, case_id: str) -> dict:
    return next(item for item in results["cases"] if item["case"] == case_id)


def hit(case_id: str, distance: float, chunk_id: str = "c1", heading_hit: bool = True) -> dict:
    """One retrieved fragment from a declared source and, if asked, from a labelled section."""
    source = CASES[case_id]["sources"][0]
    heading = "no-es-una-seccion"
    for expected in LABEL_BY_CASE[case_id]["expect"]:
        if heading_hit and expected["source"] == source:
            heading = expected["heading"]
    return {"chunk_id": chunk_id, "source": source, "heading": heading, "distance": distance}


def completed_latency(total: float) -> dict:
    return {"embedding": total / 10, "retrieval": total / 10, "generation": total / 2, "total": total}


def full_checks(case_id: str, fail_ids: tuple = (), judged: tuple = ("Ana", "Luis")) -> list:
    checks = []
    for identifier, kind in metrics.expected_checks(CASES[case_id]).items():
        checks.append({
            "id": identifier, "class": kind, "result": "fail" if identifier in fail_ids else "pass",
            "decided_by": ["rule"] if kind == "objective" else list(judged),
        })
    return checks


def passing(results: dict, case_id: str, **fields) -> dict:
    item = case_of(results, case_id)
    item.update(outcome="pass", checks=full_checks(case_id), latency_ms=completed_latency(1000.0), structured_ok=True)
    item.update(fields)
    return item


def failing(results: dict, case_id: str, **fields) -> dict:
    item = case_of(results, case_id)
    item.update(outcome="fail", checks=full_checks(case_id, fail_ids=(next(iter(metrics.expected_checks(CASES[case_id]))),)),
                latency_ms=completed_latency(1000.0), structured_ok=True)
    item.update(fields)
    return item


def blocked(results: dict, case_id: str, category: str = "connection", stage: str = "embedding", **fields) -> dict:
    item = case_of(results, case_id)
    item.update(outcome="blocked", failure_category=category, failure_stage=stage)
    item.update(fields)
    return item


def compute(results: dict) -> dict:
    return metrics.compute(results, BANK, LABELS, CATALOGUE)


def reject(test: unittest.TestCase, results: dict, field: str, secret: str | None = None) -> None:
    with test.assertRaises(metrics.ResultsError) as caught:
        metrics.validate_results(results, BANK, LABELS, CATALOGUE)
    test.assertIn(field, str(caught.exception))
    if secret:
        test.assertNotIn(secret, str(caught.exception))


class CatalogueTests(unittest.TestCase):
    def test_repository_catalogue_is_valid_and_matches_the_computed_metrics(self):
        metrics.validate_catalogue(CATALOGUE)
        self.assertEqual({item["id"] for item in CATALOGUE["metrics"]}, set(metrics.COMPUTED_IDS))

    def test_duplicate_identifier_is_rejected(self):
        catalogue = copy.deepcopy(CATALOGUE)
        catalogue["metrics"].append(copy.deepcopy(catalogue["metrics"][0]))
        with self.assertRaisesRegex(metrics.CatalogueError, "ACC-1"):
            metrics.validate_catalogue(catalogue)

    def test_every_metric_field_is_required(self):
        for field in ("id", "family", "name", "numerator", "denominator", "population", "source", "unit"):
            catalogue = copy.deepcopy(CATALOGUE)
            del catalogue["metrics"][3][field]
            with self.assertRaisesRegex(metrics.CatalogueError, field):
                metrics.validate_catalogue(catalogue)

    def test_unknown_family_and_empty_text_are_rejected(self):
        catalogue = copy.deepcopy(CATALOGUE)
        catalogue["metrics"][0]["family"] = "vibes"
        with self.assertRaisesRegex(metrics.CatalogueError, "family"):
            metrics.validate_catalogue(catalogue)
        catalogue = copy.deepcopy(CATALOGUE)
        catalogue["metrics"][0]["numerator"] = "  "
        with self.assertRaisesRegex(metrics.CatalogueError, "numerator"):
            metrics.validate_catalogue(catalogue)

    def test_a_metric_missing_from_the_catalogue_or_the_calculator_is_detected(self):
        catalogue = copy.deepcopy(CATALOGUE)
        catalogue["metrics"] = [item for item in catalogue["metrics"] if item["id"] != "AVL-1"]
        with self.assertRaisesRegex(metrics.CatalogueError, "AVL-1"):
            metrics.validate_catalogue(catalogue)
        catalogue = copy.deepcopy(CATALOGUE)
        extra = copy.deepcopy(catalogue["metrics"][0])
        extra["id"] = "ACC-9"
        catalogue["metrics"].append(extra)
        with self.assertRaisesRegex(metrics.CatalogueError, "ACC-9"):
            metrics.validate_catalogue(catalogue)

    def test_targets_are_provisional_and_cite_their_origin(self):
        for item in CATALOGUE["metrics"]:
            target = item["target"]
            if target is not None:
                self.assertIs(target["provisional"], True)
                self.assertEqual(target["origin"], "ADR-0002")


class StatisticsTests(unittest.TestCase):
    def test_wilson_interval_matches_hand_values(self):
        low, high = metrics.wilson(7, 10)
        self.assertAlmostEqual(low, 0.3968, places=4)
        self.assertAlmostEqual(high, 0.8922, places=4)
        low, high = metrics.wilson(0, 5)
        self.assertEqual(low, 0.0)
        self.assertAlmostEqual(high, 0.4345, places=3)
        low, high = metrics.wilson(5, 5)
        self.assertEqual(high, 1.0)
        self.assertAlmostEqual(low, 0.5655, places=3)
        self.assertIsNone(metrics.wilson(0, 0))

    def test_nearest_rank_percentile_and_minimum_observations(self):
        self.assertEqual(metrics.percentile(list(range(1, 11)) * 2, 0.95), 10)
        self.assertEqual(metrics.percentile(list(range(1, 21)), 0.95), 19)
        self.assertEqual(metrics.percentile(list(range(1, 11)), 0.95, minimum=20), None)
        self.assertIsNone(metrics.percentile([1, 2, 3, 4], 0.5, minimum=5))
        self.assertEqual(metrics.percentile([5, 1, 3, 4, 2], 0.5, minimum=5), 3)
        self.assertEqual(metrics.percentile([5, 1, 3, 4, 2], 1.0, minimum=5), 5)


class PopulationTests(unittest.TestCase):
    def test_blocked_and_not_run_stay_out_of_every_denominator_and_are_counted(self):
        results = base_results()
        answers = SOURCE_CASE["answer"]
        for case_id in answers[:7]:
            passing(results, case_id)
        for case_id in answers[7:10]:
            failing(results, case_id)
        for case_id in answers[10:13]:
            blocked(results, case_id)
        report = compute(results)
        acc = report["metrics"]["ACC-1"]
        self.assertEqual((acc["k"], acc["n"]), (7, 10))
        self.assertAlmostEqual(acc["rate"], 0.7)
        self.assertEqual(report["counts"]["blocked"], 3)
        self.assertEqual(report["counts"]["not_run"], 28 - 13)
        self.assertEqual(report["counts"]["pass"], 7)
        self.assertEqual(report["counts"]["fail"], 3)

    def test_clarify_and_abstain_have_their_own_rates_and_do_not_enter_the_answer_rate(self):
        results = base_results()
        passing(results, SOURCE_CASE["answer"][0])
        for case_id in SOURCE_CASE["clarify"][:4]:
            passing(results, case_id)
        failing(results, SOURCE_CASE["clarify"][4])
        failing(results, SOURCE_CASE["abstain"][0])
        passing(results, SOURCE_CASE["abstain"][1])
        report = compute(results)
        self.assertEqual((report["metrics"]["ACC-1"]["k"], report["metrics"]["ACC-1"]["n"]), (1, 1))
        groups = report["metrics"]["ACC-3"]["groups"]
        self.assertEqual((groups["clarify"]["k"], groups["clarify"]["n"]), (4, 5))
        self.assertEqual((groups["abstain"]["k"], groups["abstain"]["n"]), (1, 2))

    def test_every_rate_carries_counts_and_a_wilson_interval(self):
        results = base_results()
        for case_id in SOURCE_CASE["answer"][:5]:
            passing(results, case_id)
        failing(results, SOURCE_CASE["answer"][5])
        rate = compute(results)["metrics"]["ACC-1"]
        self.assertEqual((rate["k"], rate["n"]), (5, 6))
        low, high = metrics.wilson(5, 6)
        self.assertAlmostEqual(rate["ci95"][0], low, places=4)
        self.assertAlmostEqual(rate["ci95"][1], high, places=4)

    def test_an_empty_population_is_not_available_instead_of_zero(self):
        rate = compute(base_results())["metrics"]["ACC-1"]
        self.assertIsNone(rate["rate"])
        self.assertIs(rate["available"], False)


class AccuracyTests(unittest.TestCase):
    def test_objective_checks_are_a_separate_rate_from_judged_checks(self):
        results = base_results()
        case_a, case_b = SOURCE_CASE["answer"][:2]
        expected_b = metrics.expected_checks(CASES[case_b])
        objective_b = [i for i, kind in expected_b.items() if kind == "objective"]
        judged_b = [i for i, kind in expected_b.items() if kind == "judged"]
        passing(results, case_a)
        item = failing(results, case_b)
        item["checks"] = full_checks(case_b, fail_ids=(objective_b[-1], judged_b[0]))
        objective_a = sum(1 for kind in metrics.expected_checks(CASES[case_a]).values() if kind == "objective")
        judged_a = sum(1 for kind in metrics.expected_checks(CASES[case_a]).values() if kind == "judged")
        acc2 = compute(results)["metrics"]["ACC-2"]
        self.assertEqual((acc2["k"], acc2["n"]), (objective_a + len(objective_b) - 1, objective_a + len(objective_b)))
        self.assertEqual((acc2["judged"]["k"], acc2["judged"]["n"]), (judged_a + len(judged_b) - 1, judged_a + len(judged_b)))

    def test_a_pass_with_a_failing_check_is_rejected(self):
        results = base_results()
        item = passing(results, SOURCE_CASE["answer"][0])
        item["checks"][0]["result"] = "fail"
        reject(self, results, "cases[0].outcome")

    def test_judged_checks_must_name_who_decided_and_objective_ones_must_name_the_rule(self):
        def first(item, kind):
            return next(check for check in item["checks"] if check["class"] == kind)
        results = base_results()
        item = passing(results, SOURCE_CASE["answer"][0])
        del first(item, "judged")["decided_by"]
        reject(self, results, "decided_by")
        results = base_results()
        item = passing(results, SOURCE_CASE["answer"][0])
        first(item, "objective")["decided_by"] = ["Ana"]
        reject(self, results, "decided_by")
        results = base_results()
        item = passing(results, SOURCE_CASE["answer"][0])
        first(item, "judged")["decided_by"] = ["rule"]
        reject(self, results, "decided_by")

    def test_critical_cases_with_one_judge_are_listed(self):
        results = base_results()
        item = passing(results, CRITICAL[0])
        item["checks"] = full_checks(CRITICAL[0], judged=("Ana",))
        self.assertEqual(compute(results)["critical"]["single_decider_cases"], [CRITICAL[0]])
        item["checks"] = full_checks(CRITICAL[0], judged=("Ana", "Ana"))
        self.assertEqual(compute(results)["critical"]["single_decider_cases"], [CRITICAL[0]])
        item["checks"] = full_checks(CRITICAL[0], judged=("Ana", " ana "))
        self.assertEqual(compute(results)["critical"]["single_decider_cases"], [CRITICAL[0]])
        item["checks"] = full_checks(CRITICAL[0], judged=("Ana", "Luis"))
        self.assertEqual(compute(results)["critical"]["single_decider_cases"], [])


class RelevanceTests(unittest.TestCase):
    def test_document_and_section_hits_use_the_bank_sources_and_the_labels(self):
        results = base_results()
        case_a, case_b, case_c = ANSWERS_DIRECT[:3]
        passing(results, case_a, retrieved=[hit(case_a, 0.2)])
        passing(results, case_b, retrieved=[hit(case_b, 0.3, heading_hit=False)])
        passing(results, case_c, retrieved=[{"chunk_id": "z", "source": "no-es-de-este-caso", "heading": "x", "distance": 0.4}])
        report = compute(results)["metrics"]
        rel1, rel2 = report["REL-1"], report["REL-2"]
        self.assertEqual((rel1["k"], rel1["n"]), (2, 3))
        self.assertEqual((rel2["k"], rel2["n"]), (1, 3))

    def test_coverage_none_is_excluded_from_the_section_rate_and_listed(self):
        labels = copy.deepcopy(LABELS)
        gap = ANSWERS_DIRECT[0]
        next(label for label in labels["labels"] if label["case"] == gap)["coverage"] = "none"
        results = base_results()
        passing(results, gap, retrieved=[hit(gap, 0.2, heading_hit=False)])
        passing(results, ANSWERS_DIRECT[1], retrieved=[hit(ANSWERS_DIRECT[1], 0.2)])
        report = metrics.compute(results, BANK, labels, CATALOGUE)
        self.assertEqual((report["metrics"]["REL-2"]["k"], report["metrics"]["REL-2"]["n"]), (1, 1))
        self.assertIn(gap, report["gaps"])
        self.assertEqual((report["metrics"]["REL-1"]["k"], report["metrics"]["REL-1"]["n"]), (2, 2))

    def test_the_real_labels_list_their_corpus_gaps(self):
        report = compute(base_results())
        self.assertEqual(report["gaps"], sorted(label["case"] for label in LABELS["labels"] if label["coverage"] == "none"))
        self.assertTrue(report["gaps"])

    def test_empty_results_are_counted_per_behavior_group(self):
        results = base_results()
        passing(results, ANSWERS_DIRECT[0], retrieved=[])
        passing(results, ANSWERS_DIRECT[1], retrieved=[hit(ANSWERS_DIRECT[1], 0.2)])
        passing(results, SOURCE_CASE["abstain"][0], retrieved=[])
        groups = compute(results)["metrics"]["REL-3"]["groups"]
        self.assertEqual((groups["answer"]["k"], groups["answer"]["n"]), (1, 2))
        self.assertEqual((groups["abstain"]["k"], groups["abstain"]["n"]), (1, 1))
        self.assertEqual(groups["clarify"]["n"], 0)

    def test_confidence_is_one_minus_the_best_distance_and_skips_empty_results(self):
        results = base_results()
        results["run"]["retrieval"]["max_distance"] = None
        for index, distance in enumerate((0.1, 0.2, 0.35, 0.5, 0.65)):
            case_id = ANSWERS_DIRECT[index]
            passing(results, case_id, retrieved=[hit(case_id, distance + 0.1, "far"), hit(case_id, distance, "near")])
        passing(results, ANSWERS_DIRECT[5], retrieved=[])
        rel4 = compute(results)["metrics"]["REL-4"]
        self.assertEqual(rel4["n"], 5)
        self.assertAlmostEqual(rel4["median"], 0.65)
        self.assertAlmostEqual(rel4["q1"], 0.5)
        self.assertAlmostEqual(rel4["q3"], 0.8)

    def test_confidence_with_too_few_cases_is_not_available_and_the_mock_provider_is_flagged(self):
        results = base_results()
        results["run"]["provider"] = "mock"
        for index in range(3):
            case_id = ANSWERS_DIRECT[index]
            passing(results, case_id, retrieved=[hit(case_id, 0.4)])
        report = compute(results)
        self.assertIsNone(report["metrics"]["REL-4"]["median"])
        self.assertTrue(any("mock" in note for note in report["notes"]))

    def test_confidence_keeps_a_negative_similarity_as_computed(self):
        results = base_results()
        results["run"]["retrieval"]["max_distance"] = None
        for index in range(5):
            case_id = ANSWERS_DIRECT[index]
            passing(results, case_id, retrieved=[hit(case_id, 1.2)])
        self.assertAlmostEqual(compute(results)["metrics"]["REL-4"]["median"], -0.2)


class GroundingTests(unittest.TestCase):
    def test_citations_must_point_to_a_retrieved_fragment_of_the_same_case(self):
        results = base_results()
        case_a, case_b = ANSWERS_DIRECT[:2]
        passing(results, case_a, retrieved=[hit(case_a, 0.2, "r1"), hit(case_a, 0.3, "r2")], citations=["r1", "r2"])
        passing(results, case_b, retrieved=[hit(case_b, 0.2, "r3")], citations=["r3", "invented"])
        grd1 = compute(results)["metrics"]["GRD-1"]
        self.assertEqual((grd1["k"], grd1["n"]), (3, 4))

    def test_untraceable_figures_are_counted_and_critical_cases_are_listed(self):
        results = base_results()
        critical, other = CRITICAL[0], next(i for i in SOURCE_CASE["answer"] if i not in CRITICAL)
        failing(results, critical, figures=[{"origin": "context"}, {"origin": "untraceable"}, {"origin": "untraceable"}])
        passing(results, other, figures=[{"origin": "question"}, {"origin": "untraceable"}])
        grd2 = compute(results)["metrics"]["GRD-2"]
        self.assertEqual(grd2["total"], 3)
        self.assertEqual(grd2["by_case"], {critical: 2, other: 1})
        self.assertEqual(grd2["critical_failures"], [critical])

    def test_a_response_without_untraceable_figures_has_no_critical_failure(self):
        results = base_results()
        passing(results, CRITICAL[0], figures=[{"origin": "context"}, {"origin": "evidence"}])
        grd2 = compute(results)["metrics"]["GRD-2"]
        self.assertEqual((grd2["total"], grd2["critical_failures"]), (0, []))

    def test_evidence_reference_integrity(self):
        results = base_results()
        passing(results, ANSWERS_DIRECT[0], evidence_refs={"total": 5, "dangling": 1})
        passing(results, ANSWERS_DIRECT[1], evidence_refs={"total": 3, "dangling": 0})
        grd3 = compute(results)["metrics"]["GRD-3"]
        self.assertEqual((grd3["k"], grd3["n"]), (7, 8))

    def test_more_dangling_references_than_emitted_is_rejected(self):
        results = base_results()
        passing(results, ANSWERS_DIRECT[0], evidence_refs={"total": 1, "dangling": 2})
        reject(self, results, "evidence_refs")


class LatencyTests(unittest.TestCase):
    def build(self, values: list[float], failures: int = 0) -> dict:
        results = base_results()
        usable = [i for i in CASES][: len(values) + failures]
        for case_id, value in zip(usable, values):
            passing(results, case_id, latency_ms=completed_latency(value))
        for case_id in usable[len(values):]:
            blocked(results, case_id, category="timeout", stage="embedding")
        return results

    def test_percentiles_use_nearest_rank_over_successful_calls_only(self):
        report = compute(self.build([float(v) for v in range(1, 21)], failures=0))
        total = report["metrics"]["LAT-2"]["stages"]["total"]
        self.assertEqual(total["value"], 19)
        self.assertEqual(report["metrics"]["LAT-1"]["stages"]["total"]["value"], 10)
        self.assertEqual(report["metrics"]["LAT-3"]["stages"]["total"]["value"], 20)
        self.assertEqual(total["covers"], "successful calls only")

    def test_failed_calls_are_a_separate_rate_and_do_not_enter_the_percentiles(self):
        report = compute(self.build([float(v) for v in range(1, 21)], failures=4))
        lat4 = report["metrics"]["LAT-4"]["stages"]["embedding"]
        self.assertEqual((lat4["k"], lat4["n"]), (4, 24))
        self.assertEqual(report["metrics"]["LAT-2"]["stages"]["total"]["value"], 19)

    def test_too_few_observations_are_not_available(self):
        report = compute(self.build([1.0, 2.0, 3.0, 4.0]))
        self.assertIsNone(report["metrics"]["LAT-2"]["stages"]["total"]["value"])
        self.assertIsNone(report["metrics"]["LAT-1"]["stages"]["total"]["value"])
        report = compute(self.build([1.0, 2.0, 3.0, 4.0, 5.0]))
        self.assertEqual(report["metrics"]["LAT-1"]["stages"]["total"]["value"], 3.0)
        self.assertIsNone(report["metrics"]["LAT-2"]["stages"]["total"]["value"])

    def test_the_95th_percentile_needs_twenty_observations(self):
        values = [float(v) for v in range(1, 20)]
        self.assertIsNone(compute(self.build(values))["metrics"]["LAT-2"]["stages"]["total"]["value"])
        self.assertEqual(compute(self.build(values + [20.0]))["metrics"]["LAT-2"]["stages"]["total"]["value"], 19)

    def test_the_report_states_the_corpus_size_next_to_latency(self):
        report = compute(self.build([1.0] * 5))
        self.assertEqual(report["metrics"]["LAT-2"]["corpus"], {"documents": 3, "chunks": 120})

    def test_negative_or_boolean_latencies_are_rejected(self):
        results = self.build([1.0] * 5)
        results["cases"][0]["latency_ms"]["total"] = -1
        reject(self, results, "latency_ms")
        results = self.build([1.0] * 5)
        results["cases"][0]["latency_ms"]["total"] = True
        reject(self, results, "latency_ms")


class RobustnessAndAvailabilityTests(unittest.TestCase):
    def test_structured_rate_and_failures_by_category(self):
        results = base_results()
        for index in range(3):
            passing(results, ANSWERS_DIRECT[index], structured_ok=True)
        failing(results, ANSWERS_DIRECT[3], failure_category="schema_validation", structured_ok=False)
        for index in (4, 5):
            blocked(results, ANSWERS_DIRECT[index], category="timeout", stage="generation", latency_ms={"embedding": 10.0, "retrieval": 5.0})
        report = compute(results)["metrics"]
        self.assertEqual((report["STR-1"]["k"], report["STR-1"]["n"]), (3, 4))
        by_category = report["STR-2"]["by_category"]
        self.assertEqual((by_category["timeout"], by_category["schema_validation"], by_category["upstream"]), (2, 1, 0))

    def test_a_failure_category_outside_the_fixed_set_is_rejected(self):
        results = base_results()
        item = failing(results, ANSWERS_DIRECT[0])
        item.update(failure_category="gremlins", failure_stage="generation")
        reject(self, results, "cases[%d].failure_category" % results["cases"].index(item), secret="gremlins")

    def test_the_failure_category_and_stage_come_together(self):
        results = base_results()
        failing(results, ANSWERS_DIRECT[0])["failure_category"] = "timeout"
        reject(self, results, "failure_stage")

    def test_availability_counts_server_errors_only(self):
        results = base_results()
        results["run"]["availability"] = {"requests": 200, "server_errors": 3}
        avl = compute(results)["metrics"]["AVL-1"]
        self.assertEqual((avl["k"], avl["n"]), (197, 200))
        self.assertAlmostEqual(avl["ci95"][0], metrics.wilson(197, 200)[0], places=4)

    def test_a_run_without_requests_is_not_available_instead_of_full(self):
        results = base_results()
        results["run"]["availability"] = {"requests": 0, "server_errors": 0}
        avl = compute(results)["metrics"]["AVL-1"]
        self.assertIsNone(avl["rate"])
        self.assertIs(avl["available"], False)

    def test_more_server_errors_than_requests_is_rejected(self):
        results = base_results()
        results["run"]["availability"] = {"requests": 5, "server_errors": 6}
        reject(self, results, "run.availability")


class ResultsFormatTests(unittest.TestCase):
    def test_a_blank_run_is_valid(self):
        metrics.validate_results(base_results(), BANK, LABELS, CATALOGUE)

    def test_fields_that_could_hold_text_or_secrets_are_rejected_by_name_without_their_value(self):
        for name in ("question", "prompt", "response", "content", "answer", "api_key", "Authorization", "client_secret", "access_token", "password"):
            results = base_results()
            case_of(results, SOURCE_CASE["answer"][0])[name] = "VALOR-SECRETO-123"
            reject(self, results, name, secret="VALOR-SECRETO-123")
        results = base_results()
        results["run"]["generation"]["api_key"] = "VALOR-SECRETO-123"
        reject(self, results, "api_key", secret="VALOR-SECRETO-123")

    def test_a_results_file_for_another_bank_stops_naming_the_mismatch(self):
        results = base_results()
        results["run"]["bank"]["suite_sha256"] = "0" * 64
        reject(self, results, "run.bank.suite_sha256")

    def test_an_unknown_missing_or_duplicated_case_is_rejected_naming_the_identifier(self):
        results = base_results()
        results["cases"].append(blank_case("JUP-069-999"))
        reject(self, results, "JUP-069-999")
        results = base_results()
        removed = results["cases"].pop()
        reject(self, results, removed["case"])
        results = base_results()
        results["cases"].append(copy.deepcopy(results["cases"][0]))
        reject(self, results, results["cases"][0]["case"])

    def test_an_outdated_catalogue_version_is_not_accepted(self):
        results = base_results()
        results["catalogue_version"] = "0.9.0"
        reject(self, results, "catalogue_version")

    def test_outcomes_and_check_values_must_come_from_the_fixed_sets(self):
        results = base_results()
        results["cases"][0]["outcome"] = "maybe"
        reject(self, results, "cases[0].outcome")
        results = base_results()
        passing(results, SOURCE_CASE["answer"][0])["checks"][0]["class"] = "vibes"
        reject(self, results, "class")
        results = base_results()
        passing(results, SOURCE_CASE["answer"][0])["figures"] = [{"origin": "dream"}]
        reject(self, results, "figures")

    def test_the_run_header_requires_every_field(self):
        for path in (("commit",), ("date",), ("bank", "suite_sha256"), ("corpus", "documents"), ("corpus", "chunks"),
                     ("provider",), ("alias",), ("retrieval", "top_k"), ("generation",), ("availability", "requests")):
            results = base_results()
            node = results["run"]
            for part in path[:-1]:
                node = node[part]
            del node[path[-1]]
            reject(self, results, ".".join(("run",) + path))

    def test_a_citation_or_chunk_identifier_must_be_a_string(self):
        results = base_results()
        passing(results, ANSWERS_DIRECT[0], retrieved=[{"chunk_id": 5, "source": "x", "heading": "h", "distance": 0.1}])
        reject(self, results, "retrieved")

    def test_python_and_node_hash_the_bank_the_same_way(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is not installed")
        output = subprocess.check_output([node, str(ROOT / "tools" / "validation-questions.mjs"), "prepare"], text=True, encoding="utf8", cwd=ROOT)
        self.assertEqual(json.loads(output)["suite_sha256"], metrics.suite_digest(BANK))


class TargetsTests(unittest.TestCase):
    def test_targets_sit_next_to_the_values_and_are_never_a_verdict(self):
        results = base_results()
        for index in range(20):
            case_id = list(CASES)[index]
            passing(results, case_id, latency_ms=completed_latency(12000.0))
        report = compute(results)
        lat2 = report["metrics"]["LAT-2"]["stages"]["total"]
        self.assertEqual(lat2["target"]["value"], 10000)
        self.assertEqual(lat2["target"]["origin"], "ADR-0002")
        self.assertIs(lat2["target"]["provisional"], True)
        self.assertIs(lat2["target"]["met"], False)
        self.assertNotIn("verdict", json.dumps(report))
        markdown = metrics.render_markdown(report, CATALOGUE)
        self.assertIn("provisional", markdown)
        for word in ("rechazado", "aprobado", "rejected", "approved"):
            self.assertNotIn(word, markdown.lower())

    def test_each_target_is_compared_in_the_right_direction(self):
        results = base_results()
        for index in range(10):
            passing(results, SOURCE_CASE["answer"][index], structured_ok=True)
        self.assertIs(compute(results)["metrics"]["ACC-2"]["target"]["met"], True)
        results = base_results()
        for index in range(9):
            passing(results, SOURCE_CASE["answer"][index], structured_ok=True)
        failing(results, SOURCE_CASE["answer"][9], failure_category="schema_validation", structured_ok=False)
        self.assertIs(compute(results)["metrics"]["STR-1"]["target"]["met"], False)
        results = base_results()
        failing(results, CRITICAL[0], figures=[{"origin": "untraceable"}])
        self.assertIs(compute(results)["metrics"]["GRD-2"]["target"]["met"], False)

    def test_a_value_exactly_on_the_target_meets_it(self):
        definitions = {metric["id"]: metric for metric in CATALOGUE["metrics"]}
        for metric_id, edge, beyond in (("ACC-2", 0.9, 0.8999), ("STR-1", 0.95, 0.9499), ("LAT-2", 10000, 10000.1), ("GRD-2", 0, 1)):
            self.assertIs(metrics.target_result(definitions[metric_id], edge)["met"], True, metric_id)
            self.assertIs(metrics.target_result(definitions[metric_id], beyond)["met"], False, metric_id)
        results = base_results()
        for index in range(20):
            passing(results, list(CASES)[index], latency_ms=completed_latency(10000.0))
        report = compute(results)["metrics"]
        self.assertEqual(report["LAT-2"]["stages"]["total"]["value"], 10000.0)
        self.assertIs(report["LAT-2"]["stages"]["total"]["target"]["met"], True)

    def test_a_target_over_a_metric_that_is_not_available_is_not_judged(self):
        report = compute(base_results())
        self.assertIsNone(report["metrics"]["STR-1"]["target"]["met"])


class CliTests(unittest.TestCase):
    def run_cli(self, directory: Path, results: dict, extra: list[str] | None = None, name: str = "out") -> tuple[int, Path, Path]:
        source = directory / "results.json"
        source.write_text(json.dumps(results), encoding="utf8")
        output = directory / f"{name}.json"
        report = directory / f"{name}.md"
        code = metrics.main(["--results", str(source), "--output", str(output), "--report", str(report),
                             "--generated-at", "2026-10-05T10:00:00Z"] + (extra or []))
        return code, output, report

    def test_the_same_input_gives_byte_identical_reports(self):
        results = base_results()
        passing(results, SOURCE_CASE["answer"][0], latency_ms=completed_latency(100.0))
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            code_a, out_a, md_a = self.run_cli(directory, results, name="a")
            code_b, out_b, md_b = self.run_cli(directory, results, name="b")
            self.assertEqual((code_a, code_b), (0, 0))
            self.assertEqual(out_a.read_bytes(), out_b.read_bytes())
            self.assertEqual(md_a.read_bytes(), md_b.read_bytes())
            self.assertIn("2026-10-05T10:00:00Z", out_a.read_text(encoding="utf8"))

    def test_the_calculator_has_no_network_or_database_access(self):
        source = SCRIPT_PATH.read_text(encoding="utf8")
        imported = set(re.findall(r"^(?:import|from) ([a-z_.]+)", source, re.MULTILINE))
        self.assertFalse({name.split(".")[0] for name in imported} & {"socket", "http", "urllib", "requests", "ssl", "sqlite3", "ftplib", "smtplib", "asyncio"})
        with tempfile.TemporaryDirectory() as raw:
            source_file = Path(raw) / "results.json"
            source_file.write_text(json.dumps(base_results()), encoding="utf8")
            def blocked_call(*args, **kwargs):
                raise AssertionError("network access attempted")
            with mock.patch.object(socket, "socket", blocked_call), mock.patch.object(socket, "create_connection", blocked_call):
                self.assertEqual(metrics.main(["--results", str(source_file), "--output", str(Path(raw) / "o.json")]), 0)

    def test_an_invalid_file_exits_with_an_error_that_names_the_field_and_not_the_value(self):
        results = base_results()
        case_of(results, SOURCE_CASE["answer"][0])["question"] = "VALOR-SECRETO-123"
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            buffer = tempfile.TemporaryFile(mode="w+", encoding="utf8")
            with mock.patch.object(sys, "stderr", buffer):
                code, output, _ = self.run_cli(directory, results)
            buffer.seek(0)
            message = buffer.read()
            self.assertNotEqual(code, 0)
            self.assertIn("question", message)
            self.assertNotIn("VALOR-SECRETO-123", message)
            self.assertFalse(output.exists())

    def test_the_synthetic_example_validates_and_is_marked_as_synthetic(self):
        example = ROOT / "tools" / "fixtures" / "assistant-metrics" / "synthetic-results.json"
        data = json.loads(example.read_text(encoding="utf8"))
        self.assertIs(data["synthetic"], True)
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            code = metrics.main(["--results", str(example), "--output", str(directory / "o.json"),
                                 "--report", str(directory / "o.md"), "--generated-at", "2026-10-05T10:00:00Z"])
            self.assertEqual(code, 0)
            self.assertIn("sintetic", (directory / "o.md").read_text(encoding="utf8").lower())

    def test_the_markdown_report_prints_definitions_from_the_catalogue(self):
        results = base_results()
        passing(results, SOURCE_CASE["answer"][0])
        markdown = metrics.render_markdown(compute(results), CATALOGUE)
        for item in CATALOGUE["metrics"]:
            self.assertIn(item["id"], markdown)
        self.assertIn("k de n", markdown)
        self.assertIn("120", markdown)


class AdversarialRegressionTests(unittest.TestCase):
    def test_a_critical_case_with_an_untraceable_figure_cannot_pass(self):
        results = base_results()
        passing(results, CRITICAL[0], figures=[{"origin": "untraceable"}])
        reject(self, results, "cases[%d].outcome" % [c["case"] for c in results["cases"]].index(CRITICAL[0]))
        results = base_results()
        failing(results, CRITICAL[0], figures=[{"origin": "untraceable"}])
        report = compute(results)["metrics"]
        self.assertEqual((report["ACC-1"]["k"], report["ACC-1"]["n"]), (0, 1))
        self.assertEqual(report["GRD-2"]["critical_failures"], [CRITICAL[0]])
        other = next(i for i in SOURCE_CASE["answer"] if i not in CRITICAL)
        results = base_results()
        passing(results, other, figures=[{"origin": "untraceable"}])
        self.assertEqual(compute(results)["metrics"]["GRD-2"]["by_case"], {other: 1})

    def test_a_failed_call_carries_no_latency_for_its_stage_or_the_total(self):
        results = base_results()
        blocked(results, SOURCE_CASE["answer"][0], category="timeout", stage="generation",
                latency_ms={"embedding": 10.0, "retrieval": 5.0, "generation": 500.0})
        reject(self, results, "latency_ms.generation")
        results = base_results()
        blocked(results, SOURCE_CASE["answer"][0], category="timeout", stage="generation",
                latency_ms={"embedding": 10.0, "retrieval": 5.0, "total": 600.0})
        reject(self, results, "latency_ms.total")
        results = base_results()
        blocked(results, SOURCE_CASE["answer"][0], category="timeout", stage="generation", latency_ms={"embedding": 10.0, "retrieval": 20.0})
        lat4 = compute(results)["metrics"]["LAT-4"]["stages"]["generation"]
        self.assertEqual((lat4["k"], lat4["n"]), (1, 1))

    def test_a_passing_case_has_no_failure_and_blocked_cases_count_as_failed_calls_only(self):
        results = base_results()
        passing(results, SOURCE_CASE["answer"][0], failure_category="timeout", failure_stage="generation", structured_ok=None, latency_ms={"embedding": 10.0, "retrieval": 5.0})
        reject(self, results, "cases[0].failure_category")
        results = base_results()
        blocked = case_of(results, SOURCE_CASE["answer"][0])
        blocked.update(outcome="blocked", failure_category="connection", failure_stage="embedding")
        report = compute(results)["metrics"]
        self.assertEqual(report["STR-2"]["by_category"]["connection"], 1)
        self.assertEqual((report["LAT-4"]["stages"]["embedding"]["k"], report["LAT-4"]["stages"]["embedding"]["n"]), (1, 1))
        self.assertEqual(report["ACC-1"]["n"], 0)

    def test_the_cli_reports_hostile_input_with_exit_2_and_no_traceback(self):
        def run(path_args, text=None, results=None):
            with tempfile.TemporaryDirectory() as raw:
                source = Path(raw) / "results.json"
                source.write_text(text if text is not None else json.dumps(results), encoding="utf8")
                buffer = tempfile.TemporaryFile(mode="w+", encoding="utf8")
                with mock.patch.object(sys, "stderr", buffer):
                    code = metrics.main(["--results", str(source)] + [a.replace("{dir}", raw) for a in path_args])
                buffer.seek(0)
                return code, buffer.read()
        huge = base_results()
        huge["run"]["availability"] = {"requests": 10 ** 400, "server_errors": 0}
        code, message = run([], results=huge)
        self.assertEqual(code, 2)
        self.assertIn("run.availability.requests", message)
        code, message = run([], text="[" * 100000)
        self.assertEqual(code, 2)
        self.assertIn("results", message)
        code, message = run(["--output", "{dir}/missing/out.json"], results=base_results())
        self.assertEqual(code, 2)
        self.assertIn("--output", message)

    def test_a_report_with_non_ascii_text_reaches_a_cp1252_pipe_as_utf8(self):
        import io
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "results.json"
            source.write_text(json.dumps(base_results()), encoding="utf8")
            pipe = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")
            with mock.patch.object(sys, "stdout", pipe), mock.patch.object(metrics, "render_markdown", return_value="alias-\u03c9-\u65e5\u672c\n"):
                code = metrics.main(["--results", str(source), "--generated-at", "2026-10-05T10:00:00Z"])
            pipe.flush()
            self.assertEqual(code, 0)
            self.assertIn("alias-\u03c9-\u65e5\u672c", pipe.buffer.getvalue().decode("utf8"))

    def test_only_listed_fields_are_accepted_and_free_text_is_bounded(self):
        for name in ("question_text", "prompt_text", "response_body", "questions", "Question ", "answer_text", "body",
                     "message", "completion", "output", "pwd", "bearer", "sas", "connection_string"):
            results = base_results()
            case_of(results, SOURCE_CASE["answer"][0])[name] = "VALOR-SECRETO-123"
            reject(self, results, name.strip(), secret="VALOR-SECRETO-123")
            results = base_results()
            results["run"]["generation"][name] = "VALOR-SECRETO-123"
            reject(self, results, "run.generation", secret="VALOR-SECRETO-123")
        results = base_results()
        passing(results, ANSWERS_DIRECT[0], retrieved=[{"chunk_id": "c", "source": "finops", "heading": "x" * 1500, "distance": 0.1}])
        reject(self, results, "heading")
        results = base_results()
        results["run"]["generation"]["model_alias"] = "sk-abcdef" * 1000
        reject(self, results, "run.generation.model_alias")

    def test_no_allowed_field_name_can_hold_text_or_secrets(self):
        risky = {"question", "prompt", "response", "content", "answer", "text", "excerpt", "body", "message"}
        secret = ("key", "secret", "token", "password", "authorization", "credential")
        for group, names in metrics.ALLOWED.items():
            for name in names:
                self.assertNotIn(name, risky, group)
                if name != "max_tokens":
                    self.assertFalse(any(word in name.lower() for word in secret), f"{group}.{name}")

    def test_the_catalogue_definitions_are_pinned_to_a_hash(self):
        catalogue = copy.deepcopy(CATALOGUE)
        catalogue["metrics"][0]["numerator"] = "otra formula"
        with self.assertRaisesRegex(metrics.CatalogueError, "definitions_sha256"):
            metrics.validate_catalogue(catalogue)
        self.assertEqual(
            (CATALOGUE["catalogue_version"], CATALOGUE["definitions_sha256"]),
            PINNED_DEFINITIONS,
            "changing a definition needs a new catalogue_version: update the pin on purpose",
        )

    def test_the_mock_provider_is_recognised_whatever_its_case(self):
        for provider in ("Mock", "MOCK"):
            results = base_results()
            results["run"]["provider"] = provider
            self.assertTrue(any("mock" in note for note in compute(results)["notes"]))

    def test_retrieval_parameters_have_a_valid_range(self):
        for field, value in (("top_k", 0), ("top_k", 21), ("max_distance", -5), ("max_distance", 0), ("chunk_size", 0)):
            results = base_results()
            results["run"]["retrieval"][field] = value
            reject(self, results, "run.retrieval." + field)


class SecondPassRegressionTests(unittest.TestCase):
    ANSWER = SOURCE_CASE["answer"][0]

    def cli(self, results=None, text=None, extra=None):
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "results.json"
            source.write_text(text if text is not None else json.dumps(results), encoding="utf8")
            buffer = tempfile.TemporaryFile(mode="w+", encoding="utf8")
            args = ["--results", str(source)] + [a.replace("{dir}", raw).replace("{results}", str(source)) for a in (extra or [])]
            with mock.patch.object(sys, "stderr", buffer):
                code = metrics.main(args)
            buffer.seek(0)
            return code, buffer.read(), sorted(path.name for path in Path(raw).iterdir())

    def test_huge_integers_in_any_numeric_field_are_rejected_without_a_traceback(self):
        mutations = (
            lambda r: passing(r, self.ANSWER).update(latency_ms={"embedding": 1.0, "retrieval": 1.0, "generation": 1.0, "total": 10 ** 400}),
            lambda r: passing(r, self.ANSWER, retrieved=[{"chunk_id": "c", "source": "finops", "heading": "h", "distance": 10 ** 400}]),
            lambda r: r["run"]["retrieval"].update(max_distance=10 ** 400),
            lambda r: r["run"]["generation"].update(seed=10 ** 400),
        )
        for mutate in mutations:
            results = base_results()
            mutate(results)
            with self.assertRaises(metrics.ResultsError):
                metrics.validate_results(results, BANK, LABELS, CATALOGUE)
            code, message, _ = self.cli(results)
            self.assertEqual(code, 2)
            self.assertNotIn("Traceback", message)

    def test_a_pass_needs_one_check_per_rubric_point_of_the_case(self):
        index = [c["case"] for c in base_results()["cases"]].index(self.ANSWER)
        for outcome in ("pass", "fail"):
            results = base_results()
            case_of(results, self.ANSWER).update(outcome=outcome, checks=[], failure_category="schema_validation", structured_ok=False)
            reject(self, results, "cases[%d].checks" % index)
        results = base_results()
        item = passing(results, self.ANSWER)
        item["checks"].pop()
        reject(self, results, "cases[%d].checks" % index)
        results = base_results()
        item = passing(results, self.ANSWER)
        item["checks"].append({"id": "invented-1", "class": "objective", "result": "pass", "decided_by": ["rule"]})
        reject(self, results, "checks[%d].id" % len(item["checks"]) - 1 if False else "id")
        results = base_results()
        item = passing(results, self.ANSWER)
        item["checks"][1] = copy.deepcopy(item["checks"][0])
        reject(self, results, "checks[1].id")
        results = base_results()
        item = passing(results, self.ANSWER)
        item["checks"][0]["class"] = "judged" if item["checks"][0]["class"] == "objective" else "objective"
        reject(self, results, "checks[0].class")

    def test_cases_that_did_not_evaluate_carry_no_checks_and_a_fail_needs_a_reason(self):
        results = base_results()
        blocked(results, self.ANSWER)["checks"] = full_checks(self.ANSWER)
        reject(self, results, "checks")
        results = base_results()
        item = failing(results, self.ANSWER)
        item["checks"] = full_checks(self.ANSWER)
        reject(self, results, "outcome")
        results = base_results()
        item = blocked(results, self.ANSWER, category="schema_validation")
        item["failure_stage"] = None
        item["structured_ok"] = False
        reject(self, results, "outcome")

    def test_the_retrieval_parameters_agree_with_each_other_and_with_the_fragments(self):
        cases = [
            (lambda r: r["run"]["retrieval"].update(chunk_overlap=900), "chunk_overlap"),
            (lambda r: r["run"]["retrieval"].update(max_distance=5), "max_distance"),
            (lambda r: r["run"]["retrieval"].update(top_k=10 ** 9), "top_k"),
            (lambda r: r["run"]["corpus"].update(documents=500), "documents"),
            (lambda r: passing(r, ANSWERS_DIRECT[0], retrieved=[hit(ANSWERS_DIRECT[0], 0.1, f"c{n}") for n in range(5)]), "retrieved"),
            (lambda r: passing(r, ANSWERS_DIRECT[0], retrieved=[hit(ANSWERS_DIRECT[0], 1.9)]), "distance"),
            (lambda r: (r["run"]["corpus"].update(documents=0, chunks=0), passing(r, ANSWERS_DIRECT[0], retrieved=[hit(ANSWERS_DIRECT[0], 0.1)])), "retrieved"),
            (lambda r: passing(r, ANSWERS_DIRECT[0], retrieved=[hit(ANSWERS_DIRECT[0], 0.1, "same"), hit(ANSWERS_DIRECT[0], 0.2, "same")]), "chunk_id"),
        ]
        for mutate, field in cases:
            results = base_results()
            mutate(results)
            reject(self, results, field)

    def test_structured_output_and_failures_must_agree(self):
        combinations = (
            dict(failure_category="schema_validation", structured_ok=True),
            dict(failure_category="timeout", failure_stage="generation", structured_ok=False, latency_ms={"embedding": 10.0, "retrieval": 5.0}),
            dict(structured_ok=False),
            dict(failure_category="timeout", failure_stage="generation", structured_ok=True, latency_ms={"embedding": 10.0, "retrieval": 5.0}),
        )
        for fields in combinations:
            results = base_results()
            failing(results, self.ANSWER, **fields)
            reject(self, results, "structured_ok")
        results = base_results()
        passing(results, self.ANSWER, structured_ok=False)
        reject(self, results, "structured_ok")
        results = base_results()
        failing(results, self.ANSWER, failure_category="schema_validation", structured_ok=False,
                latency_ms={"embedding": 10.0, "retrieval": 20.0, "generation": 300.0, "total": 400.0})
        report = compute(results)["metrics"]
        self.assertEqual(report["STR-2"]["by_category"]["schema_validation"], 1)
        self.assertEqual(report["LAT-4"]["stages"]["generation"]["k"], 0)

    def test_not_run_cases_and_impossible_latencies_are_rejected(self):
        for field, value in (("retrieved", [{"chunk_id": "c", "source": "finops", "heading": "h", "distance": 0.1}]),
                             ("citations", ["x"]), ("structured_ok", True), ("latency_ms", {"total": 1.0})):
            results = base_results()
            case_of(results, self.ANSWER)[field] = value
            reject(self, results, "outcome" if field != "latency_ms" else "outcome")
        results = base_results()
        blocked(results, self.ANSWER, latency_ms={"retrieval": 5.0})
        reject(self, results, "latency_ms.retrieval")
        results = base_results()
        passing(results, self.ANSWER, latency_ms={"embedding": 90.0, "retrieval": 10.0, "generation": 10.0, "total": 50.0})
        reject(self, results, "latency_ms.total")

    def test_error_messages_never_echo_unbounded_or_control_text(self):
        results = base_results()
        results["cases"].append(blank_case("\x1b[31m" + "A" * 300000))
        with self.assertRaises(metrics.ResultsError) as caught:
            metrics.validate_results(results, BANK, LABELS, CATALOGUE)
        message = str(caught.exception)
        self.assertLess(len(message), 300)
        self.assertNotIn("\x1b", message)
        results = base_results()
        case_of(results, self.ANSWER)["\x1b[31m" + "B" * 5000] = 1
        with self.assertRaises(metrics.ResultsError) as caught:
            metrics.validate_results(results, BANK, LABELS, CATALOGUE)
        self.assertLess(len(str(caught.exception)), 300)
        self.assertNotIn("\x1b", str(caught.exception))

    def test_the_cli_refuses_unsafe_arguments_and_writes_nothing_when_one_is_wrong(self):
        code, message, _ = self.cli(base_results(), extra=["--generated-at", "x |\n# injected"])
        self.assertEqual(code, 2)
        self.assertIn("--generated-at", message)
        code, message, _ = self.cli(base_results(), extra=["--output", "{results}"])
        self.assertEqual(code, 2)
        code, message, _ = self.cli(base_results(), extra=["--output", "{dir}/same.json", "--report", "{dir}/same.json"])
        self.assertEqual(code, 2)
        code, message, _ = self.cli(base_results(), extra=["--output", "{dir}"])
        self.assertEqual(code, 2)
        self.assertIn("--output", message)
        code, message, files = self.cli(base_results(), extra=["--output", "{dir}/ok.json", "--report", "{dir}/missing/out.md"])
        self.assertEqual(code, 2)
        self.assertIn("--report", message)
        self.assertEqual(files, ["results.json"])

    def test_free_text_cannot_inject_markdown_structure_or_control_characters(self):
        self.assertEqual(metrics.md("a|b"), "a\\|b")
        for field, value in (("alias", "a|b"), ("alias", "![i](http://e/p.png)"), ("alias", "line\nbreak"), ("provider", "x y"),
                             ("commit", "[ver](http://evil.example/x) <img src=x>"), ("commit", "zzz not a hash"),
                             ("date", "ayer"), ("date", "2026-10-05\n# injected")):
            results = base_results()
            results["run"][field] = value
            reject(self, results, "run." + field)
        results = base_results()
        results["run"]["corpus"]["sha256"] = "x"
        reject(self, results, "run.corpus.sha256")

    def test_the_catalogue_hash_covers_the_families_and_targets_must_be_finite(self):
        catalogue = copy.deepcopy(CATALOGUE)
        catalogue["families"].append("extra")
        with self.assertRaisesRegex(metrics.CatalogueError, "definitions_sha256"):
            metrics.validate_catalogue(catalogue)
        catalogue = copy.deepcopy(CATALOGUE)
        next(m for m in catalogue["metrics"] if m["target"])["target"]["value"] = float("nan")
        with self.assertRaisesRegex(metrics.CatalogueError, "target"):
            metrics.validate_catalogue(catalogue)

    def test_lists_are_bounded_and_citations_are_not_repeated(self):
        results = base_results()
        passing(results, self.ANSWER, figures=[{"origin": "context"}] * 201)
        reject(self, results, "figures")
        results = base_results()
        passing(results, self.ANSWER, citations=["a"] * 101)
        reject(self, results, "citations")
        results = base_results()
        passing(results, self.ANSWER, retrieved=[hit(self.ANSWER, 0.1, "r1")], citations=["r1", "r1"])
        grd1 = compute(results)["metrics"]["GRD-1"]
        self.assertEqual((grd1["k"], grd1["n"]), (2, 2))


class ThirdPassRegressionTests(unittest.TestCase):
    ANSWER = SOURCE_CASE["answer"][0]

    def test_a_failed_call_carries_no_response_data(self):
        for field, value, expected in (
            ("citations", ["x"], "citations"),
            ("figures", [{"origin": "context"}], "citations"),
            ("evidence_refs", {"total": 3, "dangling": 0}, "evidence_refs"),
            ("retrieved", [hit(self.ANSWER, 0.1)], "retrieved"),
        ):
            results = base_results()
            blocked(results, self.ANSWER, category="connection", stage="embedding", **{field: value})
            reject(self, results, expected)
        results = base_results()
        failing(results, self.ANSWER, failure_category="timeout", failure_stage="generation", structured_ok=None, latency_ms={"embedding": 10.0, "retrieval": 5.0})
        reject(self, results, "outcome")
        results = base_results()
        blocked(results, self.ANSWER, category="timeout", stage="generation", retrieved=[hit(self.ANSWER, 0.1)],
                latency_ms={"embedding": 10.0, "retrieval": 5.0})
        self.assertEqual(compute(results)["metrics"]["STR-2"]["by_category"]["timeout"], 1)

    def test_a_schema_failure_is_a_fail_and_a_completed_call_reports_conformance_and_latency(self):
        results = base_results()
        blocked(results, self.ANSWER, category="schema_validation", stage=None, structured_ok=False)
        reject(self, results, "outcome")
        results = base_results()
        passing(results, self.ANSWER, structured_ok=None)
        reject(self, results, "structured_ok")
        results = base_results()
        passing(results, self.ANSWER, latency_ms={})
        reject(self, results, "latency_ms")

    def test_the_cli_never_overwrites_an_input_of_the_calculator(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            copies = {}
            for name, source in (("BANK_PATH", metrics.BANK_PATH), ("LABELS_PATH", metrics.LABELS_PATH), ("CATALOGUE_PATH", metrics.CATALOGUE_PATH)):
                copies[name] = directory / source.name
                shutil.copy(source, copies[name])
            original = {name: path.read_bytes() for name, path in copies.items()}
            results = directory / "results.json"
            results.write_text(json.dumps(base_results()), encoding="utf8")
            with mock.patch.multiple(metrics, **copies):
                for name, path in copies.items():
                    buffer = tempfile.TemporaryFile(mode="w+", encoding="utf8")
                    with mock.patch.object(sys, "stderr", buffer):
                        code = metrics.main(["--results", str(results), "--output", str(path)])
                    self.assertEqual(code, 2, name)
                    self.assertEqual(path.read_bytes(), original[name], name)

    def test_grounding_and_confidence_are_answer_case_rates(self):
        results = base_results()
        results["run"]["retrieval"]["max_distance"] = None
        clarify = SOURCE_CASE["clarify"][0]
        passing(results, clarify, retrieved=[hit(clarify, 0.2, "r1")], citations=["bogus"], evidence_refs={"total": 5, "dangling": 5})
        report = compute(results)["metrics"]
        self.assertEqual(report["GRD-1"]["n"], 0)
        self.assertEqual(report["GRD-3"]["n"], 0)
        self.assertEqual(report["REL-4"]["n"], 0)

    def test_a_blocked_case_must_name_its_failure_and_free_identifiers_must_be_printable(self):
        results = base_results()
        case_of(results, self.ANSWER).update(outcome="blocked")
        reject(self, results, "failure_category")
        results = base_results()
        passing(results, self.ANSWER, retrieved=[{"chunk_id": "c\x07", "source": "finops", "heading": "h", "distance": 0.1}])
        reject(self, results, "chunk_id")
        results = base_results()
        item = passing(results, self.ANSWER)
        item["checks"][-1]["decided_by"] = ["Ana\n# injected"]
        reject(self, results, "decided_by")

    def test_the_worked_example_figure_in_the_document_is_current(self):
        example = ROOT / "tools" / "fixtures" / "assistant-metrics" / "synthetic-results.json"
        report = metrics.compute(json.loads(example.read_text(encoding="utf8")), BANK, LABELS, CATALOGUE)
        acc1 = report["metrics"]["ACC-1"]
        document = (ROOT / "docs" / "validation" / "JUP-067-metrics.md").read_text(encoding="utf8")
        self.assertIn(f"`{acc1['k']} de {acc1['n']}`", document)

    def test_report_numbers_are_never_negative_zero_and_missing_values_have_no_unit(self):
        self.assertEqual(metrics.number(-0.0004), "0")
        self.assertEqual(metrics.number(0.0), "0")
        markdown = metrics.render_markdown(compute(base_results()), CATALOGUE)
        self.assertNotIn("no disponible ms", markdown)


class FourthPassRegressionTests(unittest.TestCase):
    ANSWER = SOURCE_CASE["answer"][0]

    def test_a_critical_case_with_an_ungrounded_figure_is_a_fail_for_grounding_whatever_its_checks(self):
        results = base_results()
        item = case_of(results, CRITICAL[0])
        item.update(outcome="fail", checks=full_checks(CRITICAL[0]), figures=[{"origin": "untraceable"}],
                    latency_ms=completed_latency(1000.0), structured_ok=True)
        report = compute(results)["metrics"]
        self.assertEqual(report["GRD-2"]["critical_failures"], [CRITICAL[0]])
        item["outcome"] = "pass"
        reject(self, results, "outcome")
        other = next(i for i in SOURCE_CASE["answer"] if i not in CRITICAL)
        results = base_results()
        case_of(results, other).update(outcome="fail", checks=full_checks(other), figures=[{"origin": "untraceable"}],
                                       latency_ms=completed_latency(1000.0), structured_ok=True)
        reject(self, results, "outcome")

    def test_optional_generation_settings_may_be_null(self):
        results = base_results()
        results["run"]["generation"].update(seed=None, max_tokens=None, top_p=None)
        metrics.validate_results(results, BANK, LABELS, CATALOGUE)

    def test_a_completed_call_has_every_stage_and_the_total_covers_their_sum(self):
        for missing in ("embedding", "retrieval", "generation", "total"):
            results = base_results()
            latency = completed_latency(1000.0)
            del latency[missing]
            passing(results, self.ANSWER, latency_ms=latency)
            reject(self, results, "latency_ms." + missing)
        results = base_results()
        passing(results, self.ANSWER, latency_ms={"embedding": 600.0, "retrieval": 600.0, "generation": 600.0, "total": 1000.0})
        reject(self, results, "latency_ms.total")

    def test_lat4_counts_every_completed_call_in_every_stage(self):
        results = base_results()
        for index in range(5):
            passing(results, SOURCE_CASE["answer"][index])
        blocked(results, SOURCE_CASE["answer"][5], category="timeout", stage="generation", latency_ms={"embedding": 10.0, "retrieval": 5.0})
        lat4 = compute(results)["metrics"]["LAT-4"]["stages"]
        self.assertEqual((lat4["generation"]["k"], lat4["generation"]["n"]), (1, 6))
        self.assertEqual((lat4["embedding"]["k"], lat4["embedding"]["n"]), (0, 6))

    def test_accuracy_citations_and_references_are_answer_case_rates(self):
        answer, clarify = SOURCE_CASE["answer"][0], SOURCE_CASE["clarify"][0]
        results = base_results()
        passing(results, answer)
        failing(results, clarify)
        acc2 = compute(results)["metrics"]["ACC-2"]
        objective = sum(1 for kind in metrics.expected_checks(CASES[answer]).values() if kind == "objective")
        self.assertEqual(acc2["n"], objective)
        results = base_results()
        other = SOURCE_CASE["answer"][1]
        passing(results, answer, retrieved=[hit(answer, 0.2, "r1")], citations=["r1"])
        passing(results, other, retrieved=[hit(other, 0.2, "r2")], citations=["r1"])
        grd1 = compute(results)["metrics"]["GRD-1"]
        self.assertEqual((grd1["k"], grd1["n"]), (1, 2))
        results = base_results()
        passing(results, answer, evidence_refs={"total": 4, "dangling": 0})
        passing(results, clarify, evidence_refs={"total": 5, "dangling": 5})
        grd3 = compute(results)["metrics"]["GRD-3"]
        self.assertEqual((grd3["k"], grd3["n"]), (4, 4))

    def test_judged_checks_name_at_most_two_people_and_only_critical_cases_are_listed(self):
        results = base_results()
        item = passing(results, self.ANSWER)
        judged = next(check for check in item["checks"] if check["class"] == "judged")
        judged["decided_by"] = ["Ana", "Luis", "Eva"]
        reject(self, results, "decided_by")
        non_critical = next(i for i in SOURCE_CASE["answer"] if i not in CRITICAL)
        results = base_results()
        item = passing(results, non_critical)
        item["checks"] = full_checks(non_critical, judged=("Ana",))
        self.assertEqual(compute(results)["critical"]["single_decider_cases"], [])
        results = base_results()
        item = passing(results, CRITICAL[0])
        item["checks"] = full_checks(CRITICAL[0], judged=("Ana", "ana"))
        self.assertEqual(compute(results)["critical"]["single_decider_cases"], [CRITICAL[0]])

    def test_grd2_is_not_judged_without_evaluated_critical_cases_and_a_distance_on_the_maximum_is_valid(self):
        non_critical = next(i for i in SOURCE_CASE["answer"] if i not in CRITICAL)
        results = base_results()
        passing(results, non_critical)
        self.assertIsNone(compute(results)["metrics"]["GRD-2"]["target"]["met"])
        results = base_results()
        passing(results, ANSWERS_DIRECT[0], retrieved=[hit(ANSWERS_DIRECT[0], 0.6)])
        metrics.validate_results(results, BANK, LABELS, CATALOGUE)

    def test_a_hard_link_or_a_bom_do_not_break_the_input_protection(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = directory / "results.json"
            source.write_bytes(b"\xef\xbb\xbf" + json.dumps(base_results()).encode("utf8"))
            link = directory / "link.json"
            try:
                os.link(source, link)
            except OSError:
                self.skipTest("hard links are not available")
            buffer = tempfile.TemporaryFile(mode="w+", encoding="utf8")
            with mock.patch.object(sys, "stderr", buffer):
                code = metrics.main(["--results", str(source), "--output", str(link)])
            self.assertEqual(code, 2)
            self.assertTrue(source.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(metrics.main(["--results", str(source), "--output", str(directory / "ok.json")]), 0)


class FifthPassRegressionTests(unittest.TestCase):
    ANSWER = SOURCE_CASE["answer"][0]

    def test_a_schema_failure_is_a_completed_call_and_keeps_every_latency(self):
        for missing in (None, "embedding", "retrieval", "generation", "total"):
            results = base_results()
            latency = completed_latency(1000.0)
            if missing:
                del latency[missing]
            else:
                latency = {}
            failing(results, self.ANSWER, failure_category="schema_validation", structured_ok=False, latency_ms=latency)
            reject(self, results, "latency_ms")
        results = base_results()
        failing(results, self.ANSWER, failure_category="schema_validation", structured_ok=False)
        metrics.validate_results(results, BANK, LABELS, CATALOGUE)

    def test_a_judged_check_is_never_decided_by_the_rule_whatever_its_spelling(self):
        for spelling in ("Rule", " rule", "RULE", "rule "):
            results = base_results()
            item = passing(results, self.ANSWER)
            next(check for check in item["checks"] if check["class"] == "judged")["decided_by"] = [spelling, "Ana"]
            reject(self, results, "decided_by")

    def test_the_date_must_exist_in_the_calendar(self):
        for value in ("2026-99-99", "2026-02-30"):
            results = base_results()
            results["run"]["date"] = value
            reject(self, results, "run.date")

    def test_the_report_says_when_there_is_no_distance_threshold(self):
        results = base_results()
        results["run"]["retrieval"]["max_distance"] = None
        markdown = metrics.render_markdown(compute(results), CATALOGUE)
        self.assertIn("sin umbral", markdown)
        self.assertNotIn("distancia maxima None", markdown)


class PullRequestReviewRegressionTests(unittest.TestCase):
    ANSWER = SOURCE_CASE["answer"][0]

    def test_a_failed_call_is_preceded_by_the_latency_of_the_stages_that_ran(self):
        for stage, latency, missing in (
            ("generation", {}, "embedding"),
            ("generation", {"embedding": 10.0}, "retrieval"),
            ("generation", {"retrieval": 5.0}, "embedding"),
            ("retrieval", {}, "embedding"),
        ):
            results = base_results()
            blocked(results, self.ANSWER, category="timeout", stage=stage, latency_ms=latency)
            reject(self, results, "latency_ms." + missing)
        results = base_results()
        blocked(results, self.ANSWER, category="connection", stage="embedding", latency_ms={})
        metrics.validate_results(results, BANK, LABELS, CATALOGUE)
        results = base_results()
        blocked(results, self.ANSWER, category="timeout", stage="retrieval", latency_ms={"embedding": 10.0})
        metrics.validate_results(results, BANK, LABELS, CATALOGUE)

    def test_lat4_counts_the_embedding_call_that_succeeded_before_a_later_failure(self):
        results = base_results()
        first, second = SOURCE_CASE["answer"][:2]
        blocked(results, first, category="timeout", stage="embedding")
        blocked(results, second, category="timeout", stage="generation", latency_ms={"embedding": 10.0, "retrieval": 20.0})
        embedding = compute(results)["metrics"]["LAT-4"]["stages"]["embedding"]
        self.assertEqual((embedding["k"], embedding["n"]), (1, 2))
        results = base_results()
        blocked(results, first, category="timeout", stage="embedding")
        blocked(results, second, category="timeout", stage="generation", latency_ms={})
        with self.assertRaises(metrics.ResultsError):
            metrics.validate_results(results, BANK, LABELS, CATALOGUE)

    def test_the_report_identifies_the_generation_and_the_corpus_and_bank_fingerprints(self):
        reference = base_results()
        passing(reference, self.ANSWER)
        baseline = compute(reference)
        baseline_markdown = metrics.render_markdown(baseline, CATALOGUE)
        variants = (
            ("generation", lambda r: r["run"]["generation"].update(model_alias="other-model")),
            ("generation", lambda r: r["run"]["generation"].update(temperature=0.7)),
            ("corpus", lambda r: r["run"]["corpus"].update(sha256="b" * 64)),
        )
        for name, mutate in variants:
            results = copy.deepcopy(reference)
            mutate(results)
            changed = compute(results)
            self.assertNotEqual(json.dumps(changed, sort_keys=True), json.dumps(baseline, sort_keys=True), name)
            self.assertNotEqual(metrics.render_markdown(changed, CATALOGUE), baseline_markdown, name)
        self.assertEqual(baseline["run"]["generation"], reference["run"]["generation"])
        self.assertEqual(baseline["run"]["corpus"]["sha256"], reference["run"]["corpus"]["sha256"])
        self.assertEqual(baseline["run"]["suite_sha256"], reference["run"]["bank"]["suite_sha256"])
        self.assertIn(reference["run"]["bank"]["suite_sha256"], baseline_markdown)

    def test_the_time_of_the_run_date_must_exist(self):
        for value in ("2026-10-04T99:99:99Z", "2026-10-04T24:00", "2026-10-04T12:60", "2026-10-04T12:30:61Z", "2026-10-04T7:30"):
            results = base_results()
            results["run"]["date"] = value
            reject(self, results, "run.date")
        for value in ("2026-10-04", "2026-10-04T10:00", "2026-10-04T23:59:59Z"):
            results = base_results()
            results["run"]["date"] = value
            metrics.validate_results(results, BANK, LABELS, CATALOGUE)

    def test_two_outputs_that_are_the_same_file_are_refused(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = directory / "results.json"
            source.write_text(json.dumps(base_results()), encoding="utf8")
            first, second = directory / "report.json", directory / "report.md"
            first.write_text("original", encoding="utf8")
            try:
                os.link(first, second)
            except OSError:
                self.skipTest("hard links are not available")
            buffer = tempfile.TemporaryFile(mode="w+", encoding="utf8")
            with mock.patch.object(sys, "stderr", buffer):
                code = metrics.main(["--results", str(source), "--output", str(first), "--report", str(second)])
            self.assertEqual(code, 2)
            self.assertEqual(first.read_text(encoding="utf8"), "original")


if __name__ == "__main__":
    unittest.main()
