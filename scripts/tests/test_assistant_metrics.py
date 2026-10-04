from __future__ import annotations

import copy
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


def passing(results: dict, case_id: str, **fields) -> dict:
    item = case_of(results, case_id)
    item.update(outcome="pass", checks=[
        {"id": "numbers", "class": "objective", "result": "pass", "decided_by": ["rule"]},
        {"id": "required-1", "class": "judged", "result": "pass", "decided_by": ["Ana", "Luis"]},
    ])
    item.update(fields)
    return item


def failing(results: dict, case_id: str, **fields) -> dict:
    item = case_of(results, case_id)
    item.update(outcome="fail", checks=[
        {"id": "numbers", "class": "objective", "result": "fail", "decided_by": ["rule"]},
        {"id": "required-1", "class": "judged", "result": "pass", "decided_by": ["Ana", "Luis"]},
    ])
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
            case_of(results, case_id)["outcome"] = "blocked"
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
        passing(results, case_a)
        item = failing(results, case_b)
        item["checks"] = [
            {"id": "numbers", "class": "objective", "result": "pass", "decided_by": ["rule"]},
            {"id": "forbidden", "class": "objective", "result": "fail", "decided_by": ["rule"]},
            {"id": "required-1", "class": "judged", "result": "fail", "decided_by": ["Ana"]},
        ]
        acc2 = compute(results)["metrics"]["ACC-2"]
        self.assertEqual((acc2["k"], acc2["n"]), (2, 3))
        self.assertEqual(acc2["judged"]["n"], 2)
        self.assertEqual(acc2["judged"]["k"], 1)

    def test_a_pass_with_a_failing_check_is_rejected(self):
        results = base_results()
        item = passing(results, SOURCE_CASE["answer"][0])
        item["checks"][0]["result"] = "fail"
        reject(self, results, "cases[0].outcome")

    def test_judged_checks_must_name_who_decided_and_objective_ones_must_name_the_rule(self):
        results = base_results()
        item = passing(results, SOURCE_CASE["answer"][0])
        del item["checks"][1]["decided_by"]
        reject(self, results, "decided_by")
        results = base_results()
        item = passing(results, SOURCE_CASE["answer"][0])
        item["checks"][0]["decided_by"] = ["Ana"]
        reject(self, results, "decided_by")
        results = base_results()
        item = passing(results, SOURCE_CASE["answer"][0])
        item["checks"][1]["decided_by"] = ["rule"]
        reject(self, results, "decided_by")

    def test_critical_cases_with_one_judge_are_listed(self):
        results = base_results()
        item = passing(results, CRITICAL[0])
        item["checks"][1]["decided_by"] = ["Ana"]
        report = compute(results)
        self.assertEqual(report["critical"]["single_decider_cases"], [CRITICAL[0]])
        item["checks"][1]["decided_by"] = ["Ana", "Ana"]
        self.assertEqual(compute(results)["critical"]["single_decider_cases"], [CRITICAL[0]])
        item["checks"][1]["decided_by"] = ["Ana", "Luis"]
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
        passing(results, critical, figures=[{"origin": "context"}, {"origin": "untraceable"}, {"origin": "untraceable"}])
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
            passing(results, case_id, latency_ms={"embedding": value / 10, "total": value})
        for case_id in usable[len(values):]:
            item = failing(results, case_id)
            item.update(failure_category="timeout", failure_stage="embedding")
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
        for index, ok in enumerate((True, True, True, False)):
            passing(results, ANSWERS_DIRECT[index], structured_ok=ok)
        for category in ("timeout", "timeout", "schema_validation"):
            case_id = ANSWERS_DIRECT[4 + len([x for x in results["cases"] if x["failure_category"]])]
            item = failing(results, case_id)
            item.update(failure_category=category, failure_stage="generation")
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
            passing(results, case_id, latency_ms={"total": 12000.0})
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
            passing(results, SOURCE_CASE["answer"][index], structured_ok=index < 9)
        report = compute(results)
        self.assertIs(report["metrics"]["ACC-2"]["target"]["met"], True)
        self.assertIs(report["metrics"]["STR-1"]["target"]["met"], False)
        results = base_results()
        passing(results, CRITICAL[0], figures=[{"origin": "untraceable"}])
        self.assertIs(compute(results)["metrics"]["GRD-2"]["target"]["met"], False)

    def test_a_value_exactly_on_the_target_meets_it(self):
        results = base_results()
        for index in range(9):
            passing(results, SOURCE_CASE["answer"][index])
        failing(results, SOURCE_CASE["answer"][9])
        acc2 = compute(results)["metrics"]["ACC-2"]
        self.assertEqual((acc2["k"], acc2["n"]), (9, 10))
        self.assertIs(acc2["target"]["met"], True)
        results = base_results()
        for index in range(20):
            passing(results, list(CASES)[index], structured_ok=index != 0, latency_ms={"total": 10000.0})
        report = compute(results)["metrics"]
        self.assertEqual((report["STR-1"]["k"], report["STR-1"]["n"]), (19, 20))
        self.assertIs(report["STR-1"]["target"]["met"], True)
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
        passing(results, SOURCE_CASE["answer"][0], latency_ms={"total": 100.0})
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            code_a, out_a, md_a = self.run_cli(directory, results, name="a")
            code_b, out_b, md_b = self.run_cli(directory, results, name="b")
            self.assertEqual((code_a, code_b), (0, 0))
            self.assertEqual(out_a.read_bytes(), out_b.read_bytes())
            self.assertEqual(md_a.read_bytes(), md_b.read_bytes())
            self.assertIn("2026-10-05T10:00:00Z", out_a.read_text(encoding="utf8"))

    def test_it_runs_with_every_network_call_blocked(self):
        def blocked(*args, **kwargs):
            raise AssertionError("network access attempted")
        with tempfile.TemporaryDirectory() as raw, mock.patch.object(socket, "socket", blocked), \
                mock.patch.object(socket, "create_connection", blocked):
            code, output, _ = self.run_cli(Path(raw), base_results())
            self.assertEqual(code, 0)
            self.assertTrue(output.exists())

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


if __name__ == "__main__":
    unittest.main()
