"""JUP-071 harness regression tests; fixture judgments are never model evidence."""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error


ROOT = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


robustness = load("economicon_assistant_robustness_tests", "tools/assistant-robustness.py")
SUITE, BASELINE = robustness.load_suite()
CASES = robustness.campaign(SUITE, BASELINE)
BY_ID = {case["id"]: case for case in CASES}
RULES = robustness.evaluation.load_rules()


def fixture_answer(case):
    """Numerical check fixture, not a semantically validated assistant response."""
    lines = ["Texto sintético exclusivo de la prueba del evaluador."]
    for index, number in enumerate(case["expected"]["numbers"], 1):
        aliases = RULES["aliases"].get(case["id"], {}).get(str(index), [number["label"]])
        lines.append(f"{aliases[0]}: {number['value']} {number['unit']}.")
    return "\n".join(lines)


def raw_fixture():
    config = {"generation": "unit-test-fixture", "retrieval": "none", "network": False}
    return {
        "raw_version": 1,
        "execution": {
            "kind": "template_mock", "collected_at": "2026-10-10T08:00:00+00:00",
            "harness_commit": "a" * 40, "suite_sha256": robustness.digest(SUITE),
            "harness_sha256": "c" * 64, "python_version": "3.12.0",
            "service_sha256": "b" * 64, "configuration_sha256": robustness.digest(config),
            "configuration": config, "model_execution_verified": False,
        },
        "cases": [
            {"case": case["id"], "prompt": robustness.evaluation.prompt_text(case),
             "answer": fixture_answer(case), "citations": [], "retrieved": [],
             "failure_category": None, "total_ms": None}
            for case in CASES
        ],
    }


def judgments_fixture(raw, reviewers=("fixture-person-a", "fixture-person-b")):
    return {
        "judgments_version": 1, "raw_sha256": robustness.digest(raw),
        "cases": {
            case["id"]: {
                key: [{"reviewer": name, "result": "pass", "note": "UNIT TEST ONLY"} for name in reviewers]
                for key in robustness.human_checks(case)
            } for case in CASES
        },
    }


def scored(raw=None, judgments=None, provisional=False):
    raw = raw if raw is not None else raw_fixture()
    judgments = judgments if judgments is not None else judgments_fixture(raw)
    return robustness.score(SUITE, CASES, raw, judgments, provisional)


def entry(report, case_id):
    return next(case for case in report["cases"] if case["case"] == case_id)


def cli(argv):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        status = robustness.main([str(value) for value in argv])
    return status, stdout.getvalue(), stderr.getvalue()


class SuiteTests(unittest.TestCase):
    def test_versioned_suite_and_source_hashes_validate(self):
        robustness.validate(SUITE, BASELINE)
        for source in [SUITE["baseline"], SUITE["methodology"], *SUITE["sources"].values()]:
            self.assertEqual(robustness.file_digest(ROOT / source["path"]), source["sha256"])

    def test_baseline_hash_and_reference_drift_are_rejected(self):
        for key, value in (("sha256", "0" * 64), ("suite_version", "99.0.0"), ("path", "docs/other.json")):
            suite = copy.deepcopy(SUITE)
            suite["baseline"][key] = value
            with self.subTest(key=key), self.assertRaises(robustness.Error):
                robustness.validate(suite, BASELINE)

    def test_methodology_hash_and_reference_drift_are_rejected(self):
        for key, value in (("sha256", "0" * 64), ("path", "docs/validation/README.md")):
            suite = copy.deepcopy(SUITE)
            suite["methodology"][key] = value
            with self.subTest(key=key), self.assertRaises(robustness.Error):
                robustness.validate(suite, BASELINE)

    def test_changed_corpus_bytes_cannot_retain_the_old_hash(self):
        original = robustness.file_digest
        changed_path = ROOT / SUITE["sources"]["rules"]["path"]
        with mock.patch.object(robustness, "file_digest", side_effect=lambda path: "0" * 64 if Path(path) == changed_path else original(path)):
            with self.assertRaises(robustness.Error):
                robustness.validate(SUITE, BASELINE)

    def test_duplicate_ids_unknown_baseline_and_unknown_source_are_rejected(self):
        for mutation in ("duplicate", "baseline", "source"):
            suite = copy.deepcopy(SUITE)
            if mutation == "duplicate":
                suite["cases"][1]["id"] = suite["cases"][0]["id"]
            elif mutation == "baseline":
                suite["cases"][0]["baseline_id"] = "JUP-069-999"
            else:
                suite["cases"][0]["sources"] = ["unversioned"]
            with self.subTest(mutation=mutation), self.assertRaises(robustness.Error):
                robustness.validate(suite, BASELINE)

    def test_invalid_numeric_values_are_rejected(self):
        for key, value in (("value", float("nan")), ("value", float("inf")), ("value", True), ("tolerance", -0.01)):
            suite = copy.deepcopy(SUITE)
            suite["cases"][1]["expected_numbers"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(robustness.Error):
                robustness.validate(suite, BASELINE)

    def test_campaign_contains_13_unique_baselines_and_16_pairs(self):
        self.assertEqual(len(CASES), 29)
        self.assertEqual(len({case["id"] for case in CASES}), 29)
        originals = [case for case in CASES if case["group"] == "baseline"]
        changes = [case for case in CASES if case["group"] == "perturbation"]
        self.assertEqual((len(originals), len(changes)), (13, 16))
        self.assertEqual({case["id"] for case in originals}, {case["baseline_id"] for case in changes})
        self.assertEqual({behavior: sum(c["behavior"] == behavior for c in changes) for behavior in ("answer", "clarify", "abstain")},
                         {"answer": 3, "clarify": 12, "abstain": 1})

    def test_prepared_prompts_contain_only_context_and_question(self):
        cases = copy.deepcopy(CASES)
        for case in cases:
            case["expected"] = {"required": ["SECRET-RUBRIC"], "forbidden": ["SECRET-FORBIDDEN"], "numbers": []}
            case["behavior"] = "SECRET-BEHAVIOR"
        inputs = robustness.inputs_for(cases)
        self.assertEqual(set(inputs), {"cases"})
        for original, item in zip(CASES, inputs["cases"], strict=True):
            self.assertEqual(set(item), {"id", "prompt"})
            self.assertEqual(item["prompt"], original["context"] + "\n" + original["question"])
        self.assertNotIn("SECRET-", json.dumps(inputs))


class OfflineServiceTests(unittest.TestCase):
    def test_changed_service_hash_aborts_before_import_or_possible_model_execution(self):
        original = robustness.file_digest
        for retrieval in ("empty", "fixed"):
            with self.subTest(retrieval=retrieval):
                with mock.patch.object(robustness, "file_digest", side_effect=lambda path: "0" * 64 if Path(path) == robustness.SERVICE else original(path)), \
                     mock.patch.object(robustness, "module", side_effect=AssertionError("changed service must not be imported")) as importer:
                    with self.assertRaisesRegex(robustness.Error, "service changed"):
                        robustness.offline(SUITE, CASES, retrieval)
                    importer.assert_not_called()

    def test_real_service_empty_retrieval_has_no_citations_or_model_claim(self):
        raw = robustness.offline(SUITE, CASES, "empty")
        robustness.validate_raw(raw, SUITE, CASES)
        self.assertEqual(len(raw["cases"]), 29)
        self.assertEqual(len({row["answer"] for row in raw["cases"]}), 1)
        self.assertIn("No he encontrado contexto", raw["cases"][0]["answer"])
        self.assertTrue(all(not row["retrieved"] and not row["citations"] for row in raw["cases"]))
        self.assertEqual(raw["execution"]["kind"], "template_mock")
        self.assertFalse(raw["execution"]["configuration"]["network"])
        self.assertFalse(raw["execution"]["model_execution_verified"])

    def test_real_service_fixed_retrieval_uses_corpus_and_echo_is_not_a_calculation(self):
        raw = robustness.offline(SUITE, CASES, "fixed")
        robustness.validate_raw(raw, SUITE, CASES)
        for row in raw["cases"]:
            self.assertIn(row["prompt"], row["answer"])
            self.assertEqual(row["citations"], ["fixed-corpus-fragment"])
            fragment = row["retrieved"][0]
            self.assertEqual(fragment["content"], (ROOT / fragment["source"]).read_text(encoding="utf-8")[:500])
        report = scored(raw, robustness.empty_judgments(raw))
        self.assertTrue(all(case["prompt_echo"] for case in report["cases"]))
        numeric = entry(report, "JUP-071-002")
        self.assertEqual(numeric["outcome"], "fail")
        self.assertEqual(numeric["checks"]["numbers-1"], "fail")
        self.assertTrue(numeric["missing"])
        self.assertFalse(report["generative_robustness_accepted"])


class JudgmentAndScoreTests(unittest.TestCase):
    def test_all_known_failures_from_one_person_still_leave_critical_coverage_incomplete(self):
        raw = raw_fixture()
        judgments = judgments_fixture(raw)
        judgments["cases"]["JUP-071-001"] = {
            key: [{"reviewer": "fixture-person-a", "result": "fail"}]
            for key in robustness.human_checks(BY_ID["JUP-071-001"])
        }
        report = scored(raw, judgments)
        result = entry(report, "JUP-071-001")
        self.assertEqual(result["outcome"], "fail")
        self.assertTrue(all(value == "fail" for value in result["checks"].values()))
        self.assertEqual(set(result["missing"]), set(robustness.human_checks(BY_ID["JUP-071-001"])))
        self.assertTrue(all(value == {"received": 1, "required": 2} for value in result["reviewer_coverage"].values()))
        self.assertFalse(report["assessment_complete"])

    def test_numeric_only_echo_cannot_pass_even_with_fixture_human_passes(self):
        raw = raw_fixture()
        row = next(item for item in raw["cases"] if item["case"] == "JUP-069-016")
        row["answer"] = "Pregunta: " + row["prompt"]
        result = entry(scored(raw), "JUP-069-016")
        self.assertTrue(result["prompt_echo"])
        self.assertEqual(result["outcome"], "fail")
        self.assertIn("fail", [v for k, v in result["checks"].items() if k.startswith("numbers-")])

    def test_judgments_are_bound_to_the_exact_raw_execution(self):
        raw = raw_fixture()
        judgments = judgments_fixture(raw)
        raw["cases"][0]["answer"] += " Texto alterado después del juicio."
        with self.assertRaisesRegex(robustness.Error, "exact raw"):
            scored(raw, judgments)

    def test_duplicate_reviewer_case_accents_and_whitespace_are_not_independent(self):
        for pair in (("Ana", "ana"), ("José", "Jose"), (" María  López ", "maria lopez")):
            with self.subTest(pair=pair), self.assertRaisesRegex(robustness.Error, "duplicate"):
                robustness.judge([{"reviewer": name, "result": "pass"} for name in pair], 2)

    def test_two_people_are_required_unless_marked_provisional(self):
        raw = raw_fixture()
        judgments = judgments_fixture(raw, reviewers=("fixture-person-a",))
        self.assertEqual(entry(scored(raw, judgments), "JUP-071-001")["outcome"], "not_run")
        provisional = scored(raw, judgments, provisional=True)
        self.assertEqual(entry(provisional, "JUP-071-001")["outcome"], "pass")
        self.assertTrue(provisional["provisional"])
        self.assertFalse(provisional["generative_robustness_accepted"])

    def test_one_failure_remains_a_failure_when_the_other_judgment_is_missing(self):
        raw = raw_fixture()
        judgments = robustness.empty_judgments(raw)
        judgments["cases"]["JUP-071-001"] = {"behavior": [{"reviewer": "fixture-person-a", "result": "fail"}]}
        result = entry(scored(raw, judgments), "JUP-071-001")
        self.assertEqual(result["outcome"], "fail")
        self.assertTrue(result["missing"])

    def test_forbidden_failure_wins_even_when_expected_numbers_pass(self):
        raw = raw_fixture()
        judgments = judgments_fixture(raw)
        judgments["cases"]["JUP-071-002"]["forbidden-1"][0]["result"] = "fail"
        result = entry(scored(raw, judgments), "JUP-071-002")
        self.assertEqual(result["checks"]["numbers-1"], "pass")
        self.assertEqual(result["outcome"], "fail")

    def test_behavior_check_distinguishes_useful_answer_from_universal_abstention(self):
        raw = raw_fixture()
        for row in raw["cases"]:
            row["answer"] = "No puedo responder a ninguna consulta."
        judgments = judgments_fixture(raw)
        judgments["cases"]["JUP-071-001"]["behavior"][0]["result"] = "fail"
        report = scored(raw, judgments)
        self.assertEqual(entry(report, "JUP-071-001")["outcome"], "fail")
        self.assertEqual(entry(report, "JUP-071-016")["outcome"], "pass")
        self.assertIn("answer", robustness.human_checks(BY_ID["JUP-071-001"])["behavior"])
        self.assertIn("abstain", robustness.human_checks(BY_ID["JUP-071-016"])["behavior"])

    def test_all_29_cases_stay_in_denominator_when_missing_or_blocked(self):
        raw = raw_fixture()
        raw["cases"] = [row for row in raw["cases"] if row["case"] != "JUP-071-001"]
        row = next(item for item in raw["cases"] if item["case"] == "JUP-071-002")
        row["failure_category"] = "timeout"
        row["answer"] = ""
        report = scored(raw, robustness.empty_judgments(raw))
        self.assertEqual(report["totals"]["total"], 29)
        self.assertEqual(sum(report["totals"][name] for name in robustness.OUTCOMES), 29)
        self.assertEqual(report["totals"]["pass_over_total"], 0)
        self.assertEqual(entry(report, "JUP-071-001")["outcome"], "not_run")
        self.assertEqual(entry(report, "JUP-071-001")["reason"], "missing_response")
        self.assertEqual(entry(report, "JUP-071-002")["outcome"], "blocked")
        self.assertEqual(report["groups"]["perturbation"]["answer"]["total"], 3)
        self.assertEqual(len(report["pairs"]), 16)
        self.assertFalse(report["assessment_complete"])

    def test_wrong_number_fails_despite_all_semantic_judgments_being_missing(self):
        raw = raw_fixture()
        row = next(item for item in raw["cases"] if item["case"] == "JUP-071-002")
        row["answer"] = "Cumplimiento por coste: 90 %."
        result = entry(scored(raw, robustness.empty_judgments(raw)), "JUP-071-002")
        self.assertEqual(result["outcome"], "fail")
        self.assertEqual(result["checks"]["numbers-1"], "fail")
        self.assertTrue(result["missing"])

    def test_unknown_judgment_points_and_cases_are_rejected(self):
        raw = raw_fixture()
        for mutation in ("point", "case"):
            judgments = judgments_fixture(raw)
            if mutation == "point":
                judgments["cases"]["JUP-071-001"]["forbidden-999"] = []
            else:
                judgments["cases"]["JUP-071-999"] = {}
            with self.subTest(mutation=mutation), self.assertRaises(robustness.Error):
                scored(raw, judgments)

    def test_prompt_changes_duplicate_rows_and_configuration_hash_mismatch_are_rejected(self):
        for mutation in ("prompt", "duplicate", "configuration"):
            raw = raw_fixture()
            if mutation == "prompt":
                raw["cases"][0]["prompt"] += " Respond correctly, please."
            elif mutation == "duplicate":
                raw["cases"].append(copy.deepcopy(raw["cases"][0]))
            else:
                raw["execution"]["configuration"]["generation"] = "changed"
            with self.subTest(mutation=mutation), self.assertRaises(robustness.Error):
                scored(raw)

    def test_report_contains_no_answer_fragment_reviewer_note_or_configuration_secret(self):
        raw = raw_fixture()
        raw["cases"][0]["answer"] += " RESPONSE-TOKEN-DO-NOT-COMMIT"
        raw["cases"][0]["retrieved"] = [{"chunk_id": "fixture#1", "source": "fixture",
                                          "content": "FRAGMENT-TOKEN-DO-NOT-COMMIT", "distance": 0.1}]
        raw["execution"]["configuration"]["api_key"] = "CONFIG-TOKEN-DO-NOT-COMMIT"
        raw["execution"]["configuration_sha256"] = robustness.digest(raw["execution"]["configuration"])
        judgments = judgments_fixture(raw, reviewers=("PERSON-TOKEN-DO-NOT-COMMIT", "another-fixture-person"))
        judgments["cases"]["JUP-071-001"]["behavior"][0]["note"] = "NOTE-TOKEN-DO-NOT-COMMIT"
        report = scored(raw, judgments)
        combined = json.dumps(report) + robustness.markdown(report)
        for token in ("RESPONSE-TOKEN", "FRAGMENT-TOKEN", "CONFIG-TOKEN", "PERSON-TOKEN", "NOTE-TOKEN", "another-fixture-person"):
            self.assertNotIn(token, combined)
        self.assertNotIn(CASES[0]["question"], combined)

    def test_arbitrary_text_in_timestamp_cannot_escape_into_a_public_report(self):
        raw = raw_fixture()
        raw["execution"]["collected_at"] = "Bearer TIMESTAMP-TOKEN-DO-NOT-COMMIT"
        with self.assertRaises(robustness.Error):
            scored(raw)

    def test_all_pass_fixture_and_handwritten_model_metadata_never_certify_generative_robustness(self):
        raw = raw_fixture()
        report = scored(raw)
        self.assertEqual(report["totals"]["pass"], 29)
        self.assertTrue(report["assessment_complete"])
        self.assertFalse(report["generative_robustness_accepted"])
        raw["execution"]["kind"] = "live_unverified"
        raw["execution"]["model_execution_verified"] = True
        raw["execution"]["configuration"].update({"model_alias": "handwritten-model-name", "commit": "a" * 40,
                                                  "provider": "fixture", "alias": "handwritten-model-name",
                                                  "generation": {"model_alias": "handwritten-model-name", "temperature": None}})
        raw["execution"]["configuration_sha256"] = robustness.digest(raw["execution"]["configuration"])
        report = scored(raw)
        self.assertEqual(report["totals"]["pass"], 29)
        self.assertFalse(report["model_execution_verified"])
        self.assertFalse(report["generative_robustness_accepted"])


class ComparisonTests(unittest.TestCase):
    def reports(self):
        reports = []
        for second in range(3):
            raw = raw_fixture()
            raw["execution"]["collected_at"] = f"2026-10-10T08:00:0{second}+00:00"
            reports.append(scored(raw))
        return reports

    def test_three_distinct_compatible_runs_are_required(self):
        reports = self.reports()
        result = robustness.compare(reports)
        self.assertEqual(result["executions"], 3)
        self.assertFalse(result["generative_robustness_accepted"])
        with self.assertRaisesRegex(robustness.Error, "three"):
            robustness.compare(reports[:2])
        with self.assertRaisesRegex(robustness.Error, "independent"):
            robustness.compare([reports[0], reports[0], reports[1]])

    def test_mixed_configuration_code_suite_and_provisional_status_are_rejected(self):
        for key in ("configuration_sha256", "service_sha256", "suite_sha256", "kind", "provisional", "harness_commit", "harness_sha256", "python_version"):
            reports = self.reports()
            reports[1][key] = not reports[1][key] if key == "provisional" else "different"
            with self.subTest(key=key), self.assertRaisesRegex(robustness.Error, "incompatible"):
                robustness.compare(reports)


class ReviewRegressionTests(unittest.TestCase):
    def test_suite_rejects_fewer_than_16_cases_and_missing_behavior_controls(self):
        short = copy.deepcopy(SUITE)
        short["cases"] = short["cases"][:15]
        with self.assertRaisesRegex(robustness.Error, "16"):
            robustness.validate(short, BASELINE)
        for behavior in ("answer", "clarify", "abstain"):
            suite = copy.deepcopy(SUITE)
            for case in suite["cases"]:
                if case["expected_behavior"] == behavior:
                    case["expected_behavior"] = "answer" if behavior != "answer" else "clarify"
            with self.subTest(behavior=behavior), self.assertRaisesRegex(robustness.Error, "behavior"):
                robustness.validate(suite, BASELINE)

    def test_malformed_raw_citations_fragments_distances_and_latency_cannot_pass(self):
        bad_values = [
            ("citations", "fragment-1"), ("citations", [42]),
            ("retrieved", {}), ("retrieved", ["fragment-1"]),
            ("retrieved", [{"content": "missing source and id"}]),
            ("retrieved", [{"chunk_id": "f1", "source": "fixture", "content": "text", "distance": float("nan")}]),
            ("retrieved", [{"chunk_id": "f1", "source": "fixture", "content": "text", "distance": True}]),
            ("total_ms", -1), ("total_ms", True), ("total_ms", float("inf")),
        ]
        for key, value in bad_values:
            raw = raw_fixture()
            raw["cases"][0][key] = value
            with self.subTest(field=key, value=value), self.assertRaises(robustness.Error):
                scored(raw)

    def test_repeated_perturbation_type_accumulates_all_member_outcomes(self):
        suite = copy.deepcopy(SUITE)
        group = suite["cases"][0]["perturbation"]
        suite["cases"][1]["perturbation"] = group
        cases = robustness.campaign(suite, BASELINE)
        raw = raw_fixture()
        raw["execution"]["suite_sha256"] = robustness.digest(suite)
        judgments = judgments_fixture(raw)
        judgments["cases"]["JUP-071-002"]["behavior"][0]["result"] = "fail"
        report = robustness.score(suite, cases, raw, judgments)
        self.assertEqual(report["perturbations"][group], {
            "total": 2, "pass": 1, "fail": 1, "blocked": 0, "not_run": 0, "pass_over_total": 0.5,
            "evaluated": 2, "pass_over_evaluated": 0.5,
        })
        self.assertEqual(sum(item["total"] for item in report["perturbations"].values()), 16)
        self.assertEqual(len(report["pairs"]), 16)

    def test_cli_rejects_array_json_root_without_outputs_or_traceback(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            raw, output, report = base / "raw.json", base / "result.json", base / "report.md"
            raw.write_text("[]", encoding="utf-8")
            status, stdout, stderr = cli(["score", "--raw", raw, "--output", output, "--report", report])
            self.assertEqual(status, 2)
            self.assertIn("root must be an object", stderr)
            self.assertNotIn("Traceback", stdout + stderr)
            self.assertFalse(output.exists())
            self.assertFalse(report.exists())
            self.assertEqual(raw.read_text(encoding="utf-8"), "[]")

    def test_cli_never_overwrites_raw_judgments_references_or_colliding_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            raw_file, judgments_file = base / "raw.json", base / "judgments.json"
            result, report = base / "result.json", base / "report.md"
            raw = raw_fixture()
            raw_file.write_text(json.dumps(raw), encoding="utf-8")
            judgments_file.write_text(json.dumps(judgments_fixture(raw)), encoding="utf-8")
            snapshots = {path: path.read_bytes() for path in (raw_file, judgments_file, robustness.SUITE, robustness.BASELINE, robustness.SERVICE)}
            common = ["score", "--raw", raw_file, "--judgments", judgments_file]
            arguments = [
                [*common, "--output", raw_file, "--report", report],
                [*common, "--output", result, "--report", judgments_file],
                [*common, "--output", result, "--report", result],
                [*common, "--output", base / "missing-directory/result.json", "--report", report],
                ["review-sheet", "--raw", raw_file, "--output", raw_file, "--judgments-template", judgments_file],
            ]
            for reference in (robustness.SUITE, robustness.BASELINE, robustness.SERVICE):
                arguments.append([*common, "--output", reference, "--report", report])
            # Guard real repository references even if the regression reappears.
            with mock.patch.object(robustness.evaluation, "write_text", side_effect=AssertionError("write attempted before path protection")):
                for argv in arguments:
                    with self.subTest(arguments=[str(value) for value in argv]):
                        status, _, stderr = cli(argv)
                        self.assertEqual(status, 2, stderr)
                        self.assertFalse(result.exists())
                        self.assertFalse(report.exists())
            for path, original in snapshots.items():
                self.assertEqual(path.read_bytes(), original, str(path))


class RunHeaderTests(unittest.TestCase):
    RUN_KEYS = {"run_id", "commit", "date", "provider", "alias", "suite_version", "suite_sha256", "generation"}
    LIVE_CONFIG = {"commit": "d" * 40, "corpus": {}, "provider": "gateway", "alias": "openrouter/model-x.1",
                   "retrieval": {}, "generation": {"model_alias": "model-x.1", "temperature": 0.2}}

    def live_raw(self, **overrides):
        raw = raw_fixture()
        config = {**self.LIVE_CONFIG, **overrides}
        raw["execution"].update({"kind": "live_unverified", "configuration": config,
                                 "configuration_sha256": robustness.digest(config)})
        return raw

    def test_template_report_declares_that_no_model_was_involved(self):
        raw = raw_fixture()
        run = scored(raw)["run"]
        self.assertEqual(set(run), self.RUN_KEYS)
        self.assertEqual((run["provider"], run["alias"]), ("template", "none"))
        self.assertEqual(run["generation"], {"model_alias": "plantilla-sin-modelo", "temperature": None})
        self.assertEqual(run["commit"], "a" * 40)
        self.assertEqual(run["date"], "2026-10-10T08:00:00Z")
        self.assertEqual((run["suite_version"], run["suite_sha256"]), (SUITE["suite_version"], robustness.digest(SUITE)))

    def test_live_report_takes_declared_fields_but_stays_unverified(self):
        report = scored(self.live_raw())
        run = report["run"]
        self.assertEqual((run["commit"], run["provider"], run["alias"]), ("d" * 40, "gateway", "openrouter/model-x.1"))
        self.assertEqual(run["generation"], {"model_alias": "model-x.1", "temperature": 0.2})
        self.assertFalse(report["model_execution_verified"])
        self.assertFalse(report["generative_robustness_accepted"])

    def test_run_id_is_stable_for_the_same_raw_and_differs_between_executions(self):
        raw = raw_fixture()
        other = raw_fixture()
        other["execution"]["collected_at"] = "2026-10-10T08:00:01+00:00"
        first, again, second = scored(raw)["run"]["run_id"], scored(raw)["run"]["run_id"], scored(other)["run"]["run_id"]
        self.assertEqual(first, again)
        self.assertNotEqual(first, second)
        self.assertRegex(first, r"^JUP-071-[0-9a-f]{12}$")

    def test_header_keeps_existing_fields_and_changes_no_outcome_or_denominator(self):
        raw = raw_fixture()
        report = scored(raw)
        expected_keys = {"report_version", "jup", "suite_version", "suite_sha256", "raw_sha256", "judgments_sha256", "kind",
                         "harness_commit", "harness_sha256", "python_version", "service_sha256", "configuration_sha256",
                         "collected_at", "provisional", "model_execution_verified", "generative_robustness_accepted",
                         "totals", "groups", "cases", "pairs", "perturbations", "categories", "assessment_complete"}
        self.assertEqual(set(report), expected_keys | {"run"})
        self.assertEqual(report["totals"], {"total": 29, "pass": 29, "fail": 0, "blocked": 0, "not_run": 0, "evaluated": 29,
                                            "pass_over_evaluated": 1.0, "pass_over_total": 1.0})
        withheld = scored(raw, empty_judgments := robustness.empty_judgments(raw))
        self.assertEqual((withheld["totals"]["pass"], withheld["totals"]["not_run"]), (0, 29))

    def test_declared_text_cannot_carry_arbitrary_content_into_the_public_report(self):
        for field, value in (("provider", "Bearer TOKEN-DO-NOT-COMMIT"), ("alias", "line\nbreak"),("alias", "a" * 65),
                             ("provider", ""), ("alias", None), ("commit", "not-a-sha"), ("commit", "D" * 40)):
            with self.subTest(field=field, value=value):
                with self.assertRaises(robustness.Error):
                    scored(self.live_raw(**{field: value}))

    def test_generation_is_whitelisted_and_temperature_must_be_a_real_number(self):
        for generation in ({"model_alias": "x", "temperature": True}, {"model_alias": "x", "temperature": float("nan")},
                           {"model_alias": "x", "temperature": "0.2"}, {"model_alias": "bad value", "temperature": None},
                           {"temperature": None}, "Bad Value", "x" * 70, None):
            with self.subTest(generation=generation):
                with self.assertRaises(robustness.Error):
                    scored(self.live_raw(generation=generation))
        report = scored(self.live_raw(generation={"model_alias": "x", "temperature": None, "api_key": "KEY-DO-NOT-COMMIT"}))
        self.assertNotIn("KEY-DO-NOT-COMMIT", json.dumps(report) + robustness.markdown(report))

    def test_live_header_is_validated_for_the_raw_artifact_too(self):
        raw = self.live_raw(provider="bad provider")
        with self.assertRaises(robustness.Error):
            robustness.validate_raw(raw, SUITE, CASES)
        robustness.validate_raw(self.live_raw(), SUITE, CASES)

    def test_live_configuration_that_is_not_an_object_is_a_controlled_error(self):
        for config in ([], "gateway", None, 7):
            with self.subTest(config=config):
                raw = raw_fixture()
                raw["execution"].update({"kind": "live_unverified", "configuration": config,
                                         "configuration_sha256": robustness.digest(config)})
                with self.assertRaises(robustness.Error):
                    robustness.validate_raw(raw, SUITE, CASES)
                with self.assertRaises(robustness.Error):
                    scored(raw)

    def test_collect_rejects_invalid_run_info_before_any_request(self):
        transport = TransportDouble()
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            run_info, output = base / "run.json", base / "raw.json"
            run_info.write_text(json.dumps({**self.LIVE_CONFIG, "alias": "bad alias"}), encoding="utf-8")
            with mock.patch.dict("os.environ", {"JUP071_TEST_PASSWORD": "FIXTURE-PASSWORD"}), mock.patch.object(robustness.evaluation.urllib.request, "build_opener", return_value=transport) as opener:
                status, _, stderr = cli(["collect", "--base-url", "http://transport.invalid", "--tenant", "fixture-tenant", "--password-env", "JUP071_TEST_PASSWORD", "--run-info", run_info, "--output", output])
            self.assertEqual(status, 2, stderr)
            opener.assert_not_called()
            self.assertFalse(output.exists())

    def test_markdown_shows_the_run_identity_without_the_hand_written_alias_as_proof(self):
        report = scored(self.live_raw())
        text = robustness.markdown(report)
        self.assertIn(report["run"]["run_id"], text)
        self.assertIn("no acreditada", text)


class AdversarialPassTests(unittest.TestCase):
    """Regression tests for the independent review findings."""

    def number_result(self, case_id, answer):
        raw = raw_fixture()
        for row in raw["cases"]:
            if row["case"] == case_id:
                row["answer"] = answer
        return entry(scored(raw, robustness.empty_judgments(raw)), case_id)["checks"]

    def test_paraphrased_correct_answers_pass_the_numbers_like_the_baseline(self):
        answers = {
            "JUP-071-002": ["El cumplimiento de tagging por coste es del 10 %.",
                            "El cumplimiento es del 10 %.",
                            "El cumplimiento de tagging por coste es del 10 % (100 EUR de 1.000 EUR de coste etiquetable)."],
            "JUP-071-003": ["El cumplimiento de tagging por coste es del 10 %.",
                            "El cumplimiento por coste es del 10 %, sobre 1.000 EUR de coste etiquetable."],
            "JUP-071-010": ["En julio el coste por pedido fue de 10 EUR/pedido.",
                            "El coste unitario de julio fue 10 EUR por pedido."],
        }
        for case_id, options in answers.items():
            for answer in options:
                with self.subTest(case=case_id, answer=answer):
                    checks = self.number_result(case_id, answer)
                    self.assertEqual(checks["numbers-1"], "pass")
        self.assertEqual(self.number_result("JUP-071-002", "El cumplimiento es del 90 %.")["numbers-1"], "fail")

    def test_declared_aliases_are_validated_and_hash_bound(self):
        broken = copy.deepcopy(SUITE)
        broken["cases"][1]["expected_numbers"][0]["aliases"] = ["", 3]
        with self.assertRaises(robustness.Error):
            robustness.validate(broken, BASELINE)
        for aliases in ("coste", [], {"a": 1}):
            broken = copy.deepcopy(SUITE)
            broken["cases"][1]["expected_numbers"][0]["aliases"] = aliases
            with self.subTest(aliases=aliases), self.assertRaises(robustness.Error):
                robustness.validate(broken, BASELINE)

    def test_markdown_states_both_rates_the_unavailable_denominator_and_the_pending_warning(self):
        text = robustness.markdown(scored(raw_fixture(), robustness.empty_judgments(raw_fixture())))
        self.assertIn("pass / total previsto", text)
        self.assertIn("pass / (pass + fail)", text)
        self.assertIn("no disponible", text)
        self.assertIn("juicios pendientes", text)
        complete = robustness.markdown(scored())
        self.assertIn("100,0 %", complete)
        self.assertNotIn("no disponible", complete.split("## Categorías")[0])

    def test_categories_aggregate_the_sixteen_variants_into_real_groups(self):
        report = scored(raw_fixture(), robustness.empty_judgments(raw_fixture()))
        categories = report["categories"]
        self.assertEqual(sum(c["total"] for c in categories.values()), 16)
        self.assertEqual(set(categories), {c["category"] for c in SUITE["cases"]})
        self.assertTrue(any(c["total"] > 1 for c in categories.values()))
        self.assertEqual(sum(c["pass"] + c["fail"] + c["blocked"] + c["not_run"] for c in categories.values()), 16)
        self.assertIn("allocation", robustness.markdown(report))

    def test_critical_risk_is_enforced_for_expected_figures_and_suite_version_is_semver(self):
        broken = copy.deepcopy(SUITE)
        target = next(c for c in broken["cases"] if c["expected_numbers"])
        target["risk"] = "standard"
        with self.assertRaises(robustness.Error):
            robustness.validate(broken, BASELINE)
        for version in (None, "1", "v1.0.0", "1.0"):
            broken = copy.deepcopy(SUITE)
            if version is None:
                del broken["suite_version"]
            else:
                broken["suite_version"] = version
            with self.subTest(version=version), self.assertRaises(robustness.Error):
                robustness.validate(broken, BASELINE)

    def test_malformed_suite_entries_are_controlled_errors_not_tracebacks(self):
        for mutate in (lambda s: s["cases"][1].__setitem__("expected_numbers", ["x"]),
                       lambda s: s["cases"].__setitem__(0, "not-an-object"),
                       lambda s: s["cases"][1].__setitem__("expected_numbers", [None]),
                       lambda s: s.__setitem__("cases", {})):
            broken = copy.deepcopy(SUITE)
            mutate(broken)
            with self.subTest(), self.assertRaises(robustness.Error):
                robustness.validate(broken, BASELINE)

    def test_declared_text_rejects_urls_and_key_shaped_values(self):
        for value in ("https://gw.internal.corp/v1", "sk-proj-A1b2C3d4A1b2C3d4", "SK-abc", "token-abc", "key-abc"):
            for field in ("provider", "alias"):
                with self.subTest(field=field, value=value), self.assertRaises(robustness.Error):
                    scored(RunHeaderTests().live_raw(**{field: value}))
        scored(RunHeaderTests().live_raw(alias="openrouter/model-x.1"))

    def test_provisional_review_marks_reduced_coverage_per_case_and_is_never_complete(self):
        raw = raw_fixture()
        report = scored(raw, judgments_fixture(raw, reviewers=("fixture-person-a",)), provisional=True)
        self.assertEqual(entry(report, "JUP-071-001")["outcome"], "pass")
        self.assertTrue(all(e["reduced_coverage"] for e in report["cases"]))
        self.assertFalse(report["assessment_complete"])
        full = scored(raw, judgments_fixture(raw), provisional=True)
        self.assertFalse(any(e["reduced_coverage"] for e in full["cases"]))
        self.assertTrue(full["assessment_complete"])

    def test_outputs_inside_the_repository_are_limited_to_the_evidence_folder(self):
        for target in (ROOT / "apps/backend/app/main.py", ROOT / "tools/assistant-eval.py", ROOT / "docs/validation/JUP-069-questions.json",
                       ROOT / "docs/new-file.json", ROOT / "docs/evidence/../validation/x.json"):
            with self.subTest(target=str(target)), self.assertRaises(robustness.Error):
                robustness.protect_outputs([target], [])
        robustness.protect_outputs([ROOT / "docs/evidence/JUP-071-new-report.json"], [])

    @unittest.skipUnless(sys.platform == "win32", "extended-length prefix only exists on Windows")
    def test_extended_length_windows_paths_cannot_hide_a_repository_location(self):
        hidden = Path("\\?\\" + str(ROOT / "package.json"))
        self.assertFalse(robustness.outside(hidden))
        self.assertTrue(robustness.outside(Path(tempfile.gettempdir()) / "x.json"))
        with self.assertRaises(robustness.Error):
            robustness.protect_outputs([hidden], [])


class SecondPassTests(unittest.TestCase):
    """Regression tests for the second independent review."""

    def checks(self, case_id, answer):
        raw = raw_fixture()
        for row in raw["cases"]:
            if row["case"] == case_id:
                row["answer"] = answer
        return entry(scored(raw, robustness.empty_judgments(raw)), case_id)["checks"]

    def test_a_figure_under_the_rival_figures_alias_is_not_accepted(self):
        wrong = {
            "JUP-069-005": ("El coste elegible es 10 % y el coste no asignado es 1.000 EUR.", ("numbers-1", "numbers-2")),
            "JUP-071-002": ("El coste etiquetable es del 10 %.", ("numbers-1",)),
        }
        for case_id, (answer, keys) in wrong.items():
            for key in keys:
                with self.subTest(case=case_id, key=key):
                    self.assertEqual(self.checks(case_id, answer)[key], "fail")
        right = "El coste elegible es de 1.000 EUR y el coste no asignado es del 10 %."
        self.assertEqual({k: v for k, v in self.checks("JUP-069-005", right).items() if k.startswith("numbers")},
                         {"numbers-1": "pass", "numbers-2": "pass"})
        self.assertEqual(self.checks("JUP-071-002", "El cumplimiento por coste es del 10 %.")["numbers-1"], "pass")

    def test_aliases_must_survive_normalisation_and_be_unique(self):
        for aliases in (["*"], ["`"], ["​"], ["ok", "OK "], ["a", "*"]):
            broken = copy.deepcopy(SUITE)
            broken["cases"][1]["expected_numbers"][0]["aliases"] = aliases
            with self.subTest(aliases=aliases), self.assertRaises(robustness.Error):
                robustness.validate(broken, BASELINE)

    def test_declared_values_are_lowercase_identifiers_without_credential_shapes(self):
        for value in ("ghp_" + "a" * 36, "xoxb-1234-5678-abcd", "AKIAIOSFODNN7EXAMPLE", "eyJhbGciOiJIUzI1NiJ9",
                      "my-sk-abcdef", "a3f9c2d4e5b6a7c8d9e0f1a2b3c4d5e6", "Model-X", "model_x"):
            with self.subTest(value=value), self.assertRaises(robustness.Error):
                scored(RunHeaderTests().live_raw(alias=value))
        for value in ("openrouter/model-x.1", "gpt-4o-2024-08-06", "claude-sonnet-5-5", "handwritten-model-name"):
            with self.subTest(value=value):
                scored(RunHeaderTests().live_raw(alias=value))

    def test_malformed_field_types_name_the_case_in_a_controlled_error(self):
        mutations = (("expected_behavior", ["answer"]), ("baseline_id", ["x"]), ("id", 5), ("category", None),
                     ("expected_numbers", None), ("risk", ["critical"]), ("perturbation", 3))
        for field, value in mutations:
            broken = copy.deepcopy(SUITE)
            broken["cases"][1][field] = value
            with self.subTest(field=field), self.assertRaises(robustness.Error):
                robustness.validate(broken, BASELINE)
        for field in ("category", "expected_numbers", "baseline_id"):
            broken = copy.deepcopy(SUITE)
            del broken["cases"][1][field]
            with self.subTest(missing=field), self.assertRaises(robustness.Error):
                robustness.validate(broken, BASELINE)
        broken = copy.deepcopy(SUITE)
        broken["schema_version"] = True
        with self.assertRaises(robustness.Error):
            robustness.validate(broken, BASELINE)

    def test_only_generated_reports_can_be_written_inside_the_repository(self):
        for name in ("JUP-071-validation.md", "README.md", "JUP-070-run-1-report.json", "JUP-071-report.txt"):
            with self.subTest(name=name), self.assertRaises(robustness.Error):
                robustness.protect_outputs([ROOT / "docs/evidence" / name], [])
        robustness.protect_outputs([ROOT / "docs/evidence/JUP-071-template-empty-report.json"], [])
        robustness.protect_outputs([ROOT / "docs/evidence/JUP-071-template-empty-report.md"], [])

    def test_markdown_shows_reduced_coverage_completeness_and_every_perturbation(self):
        raw = raw_fixture()
        reduced = robustness.markdown(scored(raw, judgments_fixture(raw, reviewers=("only-one",)), provisional=True))
        self.assertIn("Casos con cobertura reducida: 29", reduced)
        self.assertIn("Evaluación completa: no", reduced)
        full = robustness.markdown(scored(raw, judgments_fixture(raw), provisional=True))
        self.assertIn("Casos con cobertura reducida: 0", full)
        self.assertIn("Evaluación completa: sí", full)
        for case in SUITE["cases"]:
            self.assertIn(case["perturbation"], full)

    @unittest.skipUnless(sys.platform == "win32", "UNC administrative shares only exist on Windows")
    def test_unc_paths_cannot_reach_the_repository_through_an_administrative_share(self):
        local = str(ROOT)
        share = "\\\\localhost\\" + local[0] + "$" + local[2:]
        for target in (share + "\\docs\\validation\\JUP-071-robustness-cases.json", share + "\\docs\\new-raw.json",
                       "\\\\server\\share\\raw.json", "\\\\?\\UNC\\localhost\\" + local[0] + "$" + local[2:] + "\\x.json"):
            with self.subTest(target=target):
                self.assertFalse(robustness.outside(Path(target)))
                with self.assertRaises(robustness.Error):
                    robustness.protect_outputs([Path(target)], [])

    @unittest.skipUnless(sys.platform == "win32", "trailing dots and spaces are Windows path semantics")
    def test_trailing_spaces_and_dots_in_a_component_do_not_change_the_location(self):
        local = str(ROOT)
        for target in (local + "\\docs\\validation \\x.json", local + "\\docs\\validation.\\x.json"):
            with self.subTest(target=target):
                self.assertFalse(robustness.outside(Path(target)))
        self.assertEqual(robustness.normalised(Path(local + "\\docs\\evidence \\a.json")),
                         robustness.normalised(Path(local + "\\docs\\evidence\\a.json")))


class ThirdPassTests(unittest.TestCase):
    def test_missing_or_malformed_reference_blocks_are_controlled_errors(self):
        mutations = (lambda s: s.__delitem__("baseline"), lambda s: s.__setitem__("baseline", None),
                     lambda s: s.__setitem__("baseline", []), lambda s: s["baseline"].__delitem__("sha256"),
                     lambda s: s["baseline"].__setitem__("path", 7), lambda s: s.__delitem__("methodology"),
                     lambda s: s["methodology"].__delitem__("path"), lambda s: s["methodology"].__setitem__("sha256", None),
                     lambda s: s.__delitem__("sources"), lambda s: s.__setitem__("sources", "x"))
        for mutate in mutations:
            broken = copy.deepcopy(SUITE)
            mutate(broken)
            with self.subTest(), self.assertRaises(robustness.Error):
                robustness.validate(broken, BASELINE)

    def test_path_prefix_helpers_work_on_any_platform(self):
        self.assertEqual(robustness.stripped("\\\\?\\C:\\x\\y.json"), "C:\\x\\y.json")
        self.assertEqual(robustness.stripped("\\?\\C:\\x"), "C:\\x")
        self.assertEqual(robustness.stripped("\\\\?\\UNC\\host\\share\\x"), "\\\\host\\share\\x")
        self.assertEqual(robustness.stripped("/tmp/x"), "/tmp/x")
        with mock.patch.object(robustness.os, "name", "nt"):
            for text in ("\\\\localhost\\D$\\x", "\\\\?\\UNC\\host\\share\\x", "//host/share/x"):
                self.assertTrue(robustness.is_unc(text), text)
            self.assertFalse(robustness.is_unc("C:\\x\\y.json"))
        with mock.patch.object(robustness.os, "name", "posix"):
            for text in ("//tmp/x", "/tmp/x", "\\\\odd-file-name"):
                self.assertFalse(robustness.is_unc(text), text)


class ChatCollectorRunInfoTests(unittest.TestCase):
    """The chat collector of JUP-123 describes a run with six strings; the report header must accept that shape."""

    DOCUMENTED = {"commit": "a1b2c3d", "corpus": "corpus-demo-66", "provider": "mock", "alias": "mock",
                  "retrieval": "mock-embeddings", "generation": "mock-direct-v1"}

    def live(self, **overrides):
        return RunHeaderTests().live_raw(**{**self.DOCUMENTED, **overrides})

    def test_the_six_string_run_info_of_the_collector_is_accepted(self):
        report = scored(self.live())
        run = report["run"]
        self.assertEqual((run["commit"], run["provider"], run["alias"]), ("a1b2c3d", "mock", "mock"))
        self.assertEqual(run["generation"], {"model_alias": "mock-direct-v1", "temperature": None})
        self.assertFalse(report["model_execution_verified"])
        self.assertFalse(report["generative_robustness_accepted"])
        robustness.validate_raw(self.live(), SUITE, CASES)

    def test_a_string_generation_is_held_to_the_same_rules_as_an_object_alias(self):
        for value in ("", "Mock Direct", "MOCK", "x" * 65, "sk-abc", "token-abc", "a3f9c2d4e5b6a7c8d9e0f1a2b3c4d5e6",
                      "line\nbreak", "https://gateway.internal/v1"):
            with self.subTest(generation=value), self.assertRaises(robustness.Error):
                scored(self.live(generation=value))
        for value in (7, ["mock-direct-v1"], None, True):
            with self.subTest(generation=value), self.assertRaises(robustness.Error):
                scored(self.live(generation=value))

    def test_declared_commit_accepts_seven_to_forty_lowercase_hex_only(self):
        for commit in ("a" * 7, "a1b2c3d4e5f6", "d" * 39, "d" * 40):
            with self.subTest(commit=commit):
                self.assertEqual(scored(self.live(commit=commit))["run"]["commit"], commit)
        for commit in ("a" * 6, "d" * 41, "A1B2C3D", "SHA_DESPLEGADO_DECLARADO", " a1b2c3d", "a1b2c3d\n", "g1b2c3d", "", None, 1234567):
            with self.subTest(commit=commit), self.assertRaises(robustness.Error):
                scored(self.live(commit=commit))

    def test_relaxed_generation_and_commit_do_not_loosen_provider_alias_or_the_object_form(self):
        for field, value in (("provider", "Mock"), ("alias", "GLM-5.2"), ("alias", "has space"), ("provider", "")):
            with self.subTest(field=field, value=value), self.assertRaises(robustness.Error):
                scored(self.live(**{field: value}))
        scored(self.live(generation={"model_alias": "model-x", "temperature": 0.2}, commit="d" * 40))
        for generation in ({"model_alias": "x", "temperature": True}, {"temperature": None}, {"model_alias": "Bad Value", "temperature": None}):
            with self.subTest(generation=generation), self.assertRaises(robustness.Error):
                scored(self.live(generation=generation))

    def test_extra_collector_fields_never_reach_the_public_report(self):
        config = {**self.DOCUMENTED, "collector_manifest_sha256": "a" * 64, "collector_commit": "b" * 40,
                  "api_key": "KEY-DO-NOT-COMMIT"}
        raw = raw_fixture()
        raw["execution"].update({"kind": "live_unverified", "configuration": config,
                                 "configuration_sha256": robustness.digest(config)})
        report = scored(raw)
        self.assertNotIn("KEY-DO-NOT-COMMIT", json.dumps(report) + robustness.markdown(report))
        self.assertEqual(set(report["run"]), RunHeaderTests.RUN_KEYS)

    def test_the_template_run_is_unchanged_by_the_relaxation(self):
        run = scored(raw_fixture())["run"]
        self.assertEqual((run["provider"], run["alias"]), ("template", "none"))
        self.assertEqual(run["generation"], {"model_alias": "plantilla-sin-modelo", "temperature": None})


class FinalReviewTests(unittest.TestCase):
    """Regression tests for the fourth adversarial pass and the traceability audit."""

    HUGE = 10 ** 400

    def test_huge_integers_are_controlled_errors_in_every_numeric_field(self):
        broken = copy.deepcopy(SUITE)
        figure = next(c for c in broken["cases"] if c["expected_numbers"])["expected_numbers"][0]
        for key in ("value", "tolerance"):
            changed = copy.deepcopy(broken)
            next(c for c in changed["cases"] if c["expected_numbers"])["expected_numbers"][0][key] = self.HUGE
            with self.subTest(field=key), self.assertRaises(robustness.Error):
                robustness.validate(changed, BASELINE)
        self.assertIn("value", figure)
        with self.assertRaises(robustness.Error):
            scored(RunHeaderTests().live_raw(generation={"model_alias": "m", "temperature": self.HUGE}))
        raw = raw_fixture()
        raw["cases"][0]["retrieved"] = [{"chunk_id": "a", "source": "s", "content": "c", "distance": self.HUGE}]
        with self.assertRaises(robustness.Error):
            robustness.validate_raw(raw, SUITE, CASES)
        raw = raw_fixture()
        raw["cases"][0]["total_ms"] = self.HUGE
        with self.assertRaises(robustness.Error):
            robustness.validate_raw(raw, SUITE, CASES)

    def test_deeply_nested_json_is_a_controlled_cli_error(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            raw_file = base / "raw.json"
            raw_file.write_text('{"a":' * 20000 + "1" + "}" * 20000, encoding="utf-8")
            status, stdout, stderr = cli(["score", "--raw", raw_file, "--output", base / "r.json", "--report", base / "r.md"])
            self.assertEqual(status, 2, stderr)
            self.assertTrue(stderr.startswith("JUP-071:"), stderr)
            self.assertNotIn("Traceback", stderr)
            self.assertFalse((base / "r.json").exists())

    def test_the_compliance_variants_ask_for_the_figure_their_question_asks_for(self):
        for case_id in ("JUP-071-002", "JUP-071-003"):
            self.assertEqual(len(BY_ID[case_id]["expected"]["numbers"]), 1, case_id)
            for answer in ("El cumplimiento por coste es del 10 %.", "Solo el 10 % del coste cumple los tags mínimos."):
                with self.subTest(case=case_id, answer=answer):
                    raw = raw_fixture()
                    for row in raw["cases"]:
                        if row["case"] == case_id:
                            row["answer"] = answer
                    checks = entry(scored(raw, robustness.empty_judgments(raw)), case_id)["checks"]
                    self.assertEqual(checks["numbers-1"], "pass")
            wrong = raw_fixture()
            for row in wrong["cases"]:
                if row["case"] == case_id:
                    row["answer"] = "El cumplimiento por coste es del 90 %."
            self.assertEqual(entry(scored(wrong, robustness.empty_judgments(wrong)), case_id)["checks"]["numbers-1"], "fail")

    def test_malformed_collection_time_names_the_field(self):
        for value in ("2026-13-45T25:00:00+00:00", "2026-10-16T10:00:00+00:00 ", "x"):
            raw = raw_fixture()
            raw["execution"]["collected_at"] = value
            with self.subTest(value=value), self.assertRaises(robustness.Error) as caught:
                robustness.validate_raw(raw, SUITE, CASES)
            self.assertIn("collection time", str(caught.exception))

    def test_a_missing_git_checkout_is_a_controlled_error(self):
        failure = robustness.subprocess.CalledProcessError(128, "git")
        with mock.patch.object(robustness.subprocess, "check_output", side_effect=failure):
            with self.assertRaises(robustness.Error):
                robustness.code_commit()

    def test_collect_rejects_unexpected_run_info_fields_without_echoing_their_values(self):
        transport = TransportDouble()
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            run_info, output = base / "run.json", base / "raw.json"
            info = {**ChatCollectorRunInfoTests.DOCUMENTED, "api_key": "KEY-DO-NOT-COMMIT"}
            run_info.write_text(json.dumps(info), encoding="utf-8")
            with mock.patch.dict("os.environ", {"JUP071_TEST_PASSWORD": "FIXTURE-PASSWORD"}), mock.patch.object(robustness.evaluation.urllib.request, "build_opener", return_value=transport) as opener:
                status, stdout, stderr = cli(["collect", "--base-url", "http://transport.invalid", "--tenant", "fixture-tenant", "--password-env", "JUP071_TEST_PASSWORD", "--run-info", run_info, "--output", output])
            self.assertEqual(status, 2, stderr)
            self.assertIn("api_key", stderr)
            self.assertNotIn("KEY-DO-NOT-COMMIT", stdout + stderr)
            opener.assert_not_called()
            self.assertFalse(output.exists())

    def test_compare_reports_malformed_summaries_as_a_controlled_error(self):
        for reports in ([{}, {}, {}], [{"suite_sha256": "a"}] * 3, ["x", "y", "z"]):
            with self.subTest(reports=reports), self.assertRaises(robustness.Error):
                robustness.compare(reports)

    def test_perturbation_table_shows_the_size_of_every_group(self):
        text = robustness.markdown(scored())
        self.assertIn("| Tipo | Total | Pass | Fail | Blocked | Not run |", text)

    def test_timeouts_and_server_errors_are_recorded_once_as_blocked(self):
        class TimeoutTransport(TransportDouble):
            def open(self, request, timeout):
                if request.full_url.endswith("/messages") and self.messages == 0:
                    self.messages += 1
                    self.requests.append((request.full_url, json.loads(request.data), dict(request.header_items()), timeout))
                    raise TimeoutError("fixture timeout")
                return super().open(request, timeout)

        for label, transport, categories in (("500", TransportDouble(first_message_status=500), {"upstream"}),
                                              ("timeout", TimeoutTransport(), {"timeout"})):
            with self.subTest(failure=label):
                raw = robustness.evaluation.collect_cases("http://transport.invalid", "fixture@example.invalid", "FIXTURE-PASSWORD", "fixture-tenant", robustness.inputs_for(CASES), opener=transport)
                raw["execution"] = raw_fixture()["execution"]
                self.assertIn(raw["cases"][0]["failure_category"], categories)
                self.assertEqual(transport.messages, 29)
                report = scored(raw, robustness.empty_judgments(raw))
                self.assertEqual(report["cases"][0]["outcome"], "blocked")
                self.assertEqual(report["totals"]["blocked"], 1)
                self.assertEqual(report["totals"]["total"], 29)

    def test_one_passing_case_among_unreviewed_ones_is_not_a_passing_suite(self):
        raw = raw_fixture()
        judgments = robustness.empty_judgments(raw)
        judgments["cases"]["JUP-071-001"] = judgments_fixture(raw)["cases"]["JUP-071-001"]
        report = scored(raw, judgments)
        self.assertEqual((report["totals"]["pass"], report["totals"]["not_run"], report["totals"]["evaluated"]), (1, 28, 1))
        text = robustness.markdown(report)
        self.assertIn("pass / total previsto: 3,4 %", text)
        self.assertIn("pass / (pass + fail): 100,0 %", text)
        self.assertIn("Evaluación completa: no", text)

    def test_the_run_header_never_changes_an_outcome_or_a_denominator(self):
        first = scored(RunHeaderTests().live_raw(provider="gateway", alias="model-a"))
        second = scored(RunHeaderTests().live_raw(provider="another", alias="model-b"))
        for key in ("totals", "groups", "categories", "perturbations", "pairs", "assessment_complete"):
            self.assertEqual(first[key], second[key], key)
        self.assertEqual([c["outcome"] for c in first["cases"]], [c["outcome"] for c in second["cases"]])
        self.assertEqual(sum(c["total"] for c in first["categories"].values()), 16)

    @unittest.skipUnless(sys.platform == "win32", "case-insensitive file systems are a Windows property here")
    def test_case_differences_cannot_hide_a_repository_location(self):
        shouted = Path(str(ROOT).upper()) / "DOCS" / "VALIDATION" / "JUP-071-ROBUSTNESS-CASES.JSON"
        with self.assertRaises(robustness.Error):
            robustness.protect_outputs([shouted], [])
        self.assertFalse(robustness.outside(shouted))


class FifthPassTests(unittest.TestCase):
    """Regression tests for the targeted fifth pass."""

    def run_collect(self, info):
        transport = TransportDouble()
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            run_info, output = base / "run.json", base / "raw.json"
            run_info.write_text(json.dumps(info), encoding="utf-8")
            with mock.patch.dict("os.environ", {"JUP071_TEST_PASSWORD": "FIXTURE-PASSWORD"}), mock.patch.object(robustness.evaluation.urllib.request, "build_opener", return_value=transport) as opener:
                status, stdout, stderr = cli(["collect", "--base-url", "http://transport.invalid", "--tenant", "fixture-tenant", "--password-env", "JUP071_TEST_PASSWORD", "--run-info", run_info, "--output", output])
            return status, stdout + stderr, opener.call_count, output.exists()

    def test_prepare_never_writes_the_prompts_inside_the_repository(self):
        for name in ("jup-071-x-report.json", "JUP-071-x-report.md"):
            with self.subTest(name=name), mock.patch.object(robustness.evaluation, "write_private") as writer:
                status, _, stderr = cli(["prepare", "--output", ROOT / "docs/evidence" / name])
                self.assertEqual(status, 2, stderr)
                writer.assert_not_called()

    def test_nested_run_info_values_cannot_smuggle_extra_fields(self):
        base = ChatCollectorRunInfoTests.DOCUMENTED
        hostile = (
            ("generation", {"model_alias": "m-1", "temperature": None, "api_key": "LEAK-SECRET-VALUE"}),
            ("retrieval", {"token": "LEAK-SECRET-VALUE"}),
            ("retrieval", {"top_k": {"nested": "LEAK-SECRET-VALUE"}}),
            ("corpus", "x" * 5000),
            ("corpus", ["LEAK-SECRET-VALUE"]),
            ("retrieval", {"k" + str(n): n for n in range(40)}),
        )
        for field, value in hostile:
            with self.subTest(field=field):
                status, output, requests, written = self.run_collect({**base, field: value})
                self.assertEqual(status, 2, output)
                self.assertEqual((requests, written), (0, False))
                self.assertNotIn("LEAK-SECRET-VALUE", output)
                self.assertIn(field, output)

    def test_flat_descriptive_run_info_is_still_accepted(self):
        base = ChatCollectorRunInfoTests.DOCUMENTED
        for info in ({**base}, {**base, "corpus": {"documents": 4, "chunks": 66, "embedding": "mock"},
                                "retrieval": {"top_k": 4, "max_distance": None},
                                "generation": {"model_alias": "model-x", "temperature": 0.2}}):
            with self.subTest(info=info):
                status, output, requests, written = self.run_collect(info)
                self.assertEqual(status, 0, output)
                self.assertTrue(written)

    def test_every_perturbation_row_states_its_own_size(self):
        text = robustness.markdown(scored(raw_fixture(), robustness.empty_judgments(raw_fixture())))
        rows = {line.split("|")[1].strip(): [cell.strip() for cell in line.split("|")[2:-1]]
                for line in text.splitlines() if line.startswith("| ") and line.split("|")[1].strip() in
                {c["perturbation"] for c in SUITE["cases"]}}
        self.assertEqual(len(rows), 16)
        for name, cells in rows.items():
            self.assertEqual(len(cells), 5, name)
            self.assertEqual(cells[0], "1", name)

    def test_a_third_reviewer_for_one_point_is_refused(self):
        raw = raw_fixture()
        judgments = judgments_fixture(raw)
        judgments["cases"]["JUP-071-001"]["behavior"].append({"reviewer": "fixture-person-c", "result": "pass", "note": "UNIT TEST ONLY"})
        with self.assertRaises(robustness.Error) as caught:
            scored(raw, judgments)
        self.assertIn("at most two", str(caught.exception))


class FakeResponse:
    def __init__(self, body, status=200):
        self.body, self.status = body, status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.body).encode("utf-8")


class TransportDouble:
    """Explicit local HTTP double: exercises production collector, never a model."""
    def __init__(self, first_message_status=None):
        self.requests = []
        self.conversations = 0
        self.messages = 0
        self.first_message_status = first_message_status

    def open(self, request, timeout):
        self.requests.append((request.full_url, json.loads(request.data), dict(request.header_items()), timeout))
        if request.full_url.endswith("/auth/login"):
            return FakeResponse({"access_token": "TRANSPORT-TOKEN-DO-NOT-COMMIT"})
        if request.full_url.endswith("/assistant/conversations"):
            self.conversations += 1
            return FakeResponse({"id": f"isolated-{self.conversations}"}, 201)
        self.messages += 1
        if self.messages == 1 and self.first_message_status:
            raise urllib.error.HTTPError(request.full_url, self.first_message_status, "fixture error", {}, io.BytesIO())
        return FakeResponse({"assistant_message": {"content": "Transport fixture response.", "metadata": {"citations": []}}, "retrieved_context": []}, 201)


class CliAndTransportTests(unittest.TestCase):
    def test_prepare_and_offline_refuse_repository_paths_without_writing(self):
        target = ROOT / "docs/validation/blocked-private-test.json"
        self.assertFalse(target.exists())
        for argv in (["prepare", "--output", target], ["offline", "--retrieval", "empty", "--output", target]):
            with self.subTest(command=argv[0]):
                status, _, _ = cli(argv)
                self.assertEqual(status, 2)
                self.assertFalse(target.exists())

    def test_private_prepare_and_review_sheet_work_outside_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            prepared, raw_file, review, judgments = (base / name for name in ("inputs.json", "raw.json", "review.md", "judgments.json"))
            self.assertEqual(cli(["prepare", "--output", prepared])[0], 0)
            self.assertEqual(len(json.loads(prepared.read_text(encoding="utf-8"))["cases"]), 29)
            raw = raw_fixture()
            raw_file.write_text(json.dumps(raw), encoding="utf-8")
            self.assertEqual(cli(["review-sheet", "--raw", raw_file, "--output", review, "--judgments-template", judgments])[0], 0)
            self.assertIn(robustness.digest(raw), review.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(judgments.read_text(encoding="utf-8"))["raw_sha256"], robustness.digest(raw))
            blocked = ROOT / "docs/validation/blocked-review-test.md"
            status, _, _ = cli(["review-sheet", "--raw", raw_file, "--output", blocked, "--judgments-template", judgments])
            self.assertEqual(status, 2)
            self.assertFalse(blocked.exists())

    def test_jup070_transport_creates_a_fresh_conversation_per_exact_prompt(self):
        transport = TransportDouble()
        raw = robustness.evaluation.collect_cases("http://transport.invalid", "fixture@example.invalid", "FIXTURE-PASSWORD", "fixture-tenant", robustness.inputs_for(CASES), timeout=7, opener=transport)
        self.assertEqual((transport.conversations, transport.messages), (29, 29))
        self.assertEqual(len(transport.requests), 59)
        messages = [item for item in transport.requests if item[0].endswith("/messages")]
        self.assertEqual(len({item[0] for item in messages}), 29)
        self.assertEqual([item[1]["content"] for item in messages], [robustness.evaluation.prompt_text(case) for case in CASES])
        self.assertTrue(all(item[3] == 7 for item in messages))
        self.assertEqual(len(raw["cases"]), 29)
        self.assertNotIn("FIXTURE-PASSWORD", json.dumps(raw))
        self.assertNotIn("TRANSPORT-TOKEN", json.dumps(raw))

    def test_jup070_authentication_failure_is_a_blocked_case_in_robustness(self):
        transport = TransportDouble(first_message_status=401)
        raw = robustness.evaluation.collect_cases("http://transport.invalid", "fixture@example.invalid", "FIXTURE-PASSWORD", "fixture-tenant", robustness.inputs_for(CASES), opener=transport)
        raw["execution"] = raw_fixture()["execution"]
        self.assertEqual(raw["cases"][0]["failure_category"], "authentication")
        report = scored(raw, robustness.empty_judgments(raw))
        self.assertEqual(report["cases"][0]["outcome"], "blocked")
        self.assertEqual(report["totals"]["total"], 29)

    def test_collect_cli_uses_production_transport_and_marks_it_unverified(self):
        transport = TransportDouble()
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            run_info, output = base / "run.json", base / "raw.json"
            run_info.write_text(json.dumps({"commit": "a" * 40, "corpus": {}, "provider": "fixture", "alias": "fixture", "retrieval": {}, "generation": {"model_alias": "fixture", "temperature": None}}), encoding="utf-8")
            with mock.patch.dict("os.environ", {"JUP071_TEST_PASSWORD": "FIXTURE-PASSWORD"}), mock.patch.object(robustness.evaluation.urllib.request, "build_opener", return_value=transport):
                status, stdout, stderr = cli(["collect", "--base-url", "http://transport.invalid", "--tenant", "fixture-tenant", "--password-env", "JUP071_TEST_PASSWORD", "--run-info", run_info, "--output", output])
            self.assertEqual(status, 0, stderr)
            raw = json.loads(output.read_text(encoding="utf-8"))
            robustness.validate_raw(raw, SUITE, CASES)
            self.assertEqual(raw["execution"]["kind"], "live_unverified")
            self.assertFalse(raw["execution"]["model_execution_verified"])
            self.assertEqual(len(raw["cases"]), 29)
            self.assertNotIn("FIXTURE-PASSWORD", stdout + stderr + json.dumps(raw))


class UnmeasuredDistanceTests(unittest.TestCase):
    """S1: evidence without a measured distance is kept as such, never as a zero."""

    FRAGMENT = {"chunk_id": "f1", "source": "docs/x.md", "content": "texto", "distance": None}

    def test_the_tool_declares_that_it_accepts_unmeasured_distance(self):
        self.assertIs(robustness.ACCEPTS_UNMEASURED_DISTANCE, True)

    def test_null_distance_is_valid_and_scores_like_any_other_row(self):
        raw = raw_fixture()
        raw["cases"][0]["retrieved"] = [dict(self.FRAGMENT)]
        report = scored(raw)
        self.assertEqual(report["totals"]["total"], 29)

    def test_a_missing_or_invalid_distance_is_still_rejected(self):
        for fragment in ({k: v for k, v in self.FRAGMENT.items() if k != "distance"},
                         {**self.FRAGMENT, "distance": "0.1"}, {**self.FRAGMENT, "distance": True},
                         {**self.FRAGMENT, "distance": float("nan")}):
            raw = raw_fixture()
            raw["cases"][0]["retrieved"] = [fragment]
            with self.subTest(fragment=fragment), self.assertRaises(robustness.Error):
                scored(raw)

    def test_public_evidence_is_optional_and_validated(self):
        good = [{"id": "e1", "kind": "corpus", "source": "docs/x.md", "content": "texto", "distance": None}]
        raw = raw_fixture()
        raw["cases"][0]["public_evidence"] = good
        self.assertEqual(scored(raw)["totals"]["total"], 29)
        for bad in ("e1", {}, ["e1"], [{"kind": "corpus"}], [{"id": 1, "kind": "corpus"}],
                    [{"id": "e1", "kind": "corpus", "distance": "0.1"}],
                    [{"id": "e1", "kind": "corpus", "distance": float("inf")}]):
            raw = raw_fixture()
            raw["cases"][0]["public_evidence"] = bad
            with self.subTest(bad=bad), self.assertRaises(robustness.Error):
                scored(raw)

    def test_review_sheet_shows_public_evidence_and_unmeasured_distance(self):
        raw = raw_fixture()
        raw["cases"][0]["retrieved"] = [dict(self.FRAGMENT)]
        raw["cases"][0]["public_evidence"] = [{"id": "e1", "kind": "corpus", "source": "docs/x.md", "content": "EVIDENCIA-VISIBLE", "distance": None}]
        text = robustness.sheet(CASES, raw)
        self.assertIn("EVIDENCIA-VISIBLE", text)
        self.assertIn('"distance": null', text)
        plain = robustness.sheet(CASES, raw_fixture())
        self.assertNotIn("public_evidence", plain)


class RowsContractTests(unittest.TestCase):
    """S2: the score report can be emitted as the dashboard's rows-v1 contract."""

    RESULT_KEYS = ("measure_type", "grp", "metric_id", "behavior", "status", "count", "value", "unit",
                   "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected")
    RUN_KEYS = ("run_id", "source", "run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
                "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic")

    def rows(self, raw=None, judgments=None):
        return robustness.rows_v1(scored(raw, judgments))

    def test_shape_and_run_identity(self):
        document = self.rows()
        self.assertEqual(document["contract_version"], 1)
        self.assertEqual(tuple(document["run"]), self.RUN_KEYS)
        report = scored()
        run = document["run"]
        self.assertEqual((run["run_id"], run["source"], run["suite"], run["synthetic"]),
                         (report["run"]["run_id"], "JUP-071", "JUP-071", True))
        self.assertEqual((run["run_at"], run["commit"], run["suite_sha256"]),
                         (report["run"]["date"], report["run"]["commit"], report["suite_sha256"]))
        self.assertIsNone(run["prompt_sha256"])
        for row in document["results"]:
            self.assertEqual(tuple(row), self.RESULT_KEYS)

    def test_case_states_carry_counts_and_never_a_value(self):
        document = self.rows()
        total = [r for r in document["results"] if (r["grp"], r["behavior"]) == ("cases", "all")]
        self.assertEqual({r["status"] for r in total}, set(robustness.OUTCOMES))
        self.assertEqual(sum(r["count"] for r in total), 29)
        for row in total:
            self.assertIsNone(row["value"])
            self.assertEqual(row["denominator"], 29)
            self.assertEqual(row["judgment"], "human" if row["status"] in ("pass", "fail") else "automatic")

    def test_unmeasured_rate_is_null_not_zero(self):
        empty = robustness.score(SUITE, CASES, raw_fixture(), robustness.empty_judgments(raw_fixture()))
        document = robustness.rows_v1(empty)
        rate = next(r for r in document["results"] if r["metric_id"] == "pass_over_evaluated")
        if empty["totals"]["evaluated"] == 0:
            self.assertEqual((rate["status"], rate["value"], rate["denominator"]), ("not_measured", None, 0))
        total = next(r for r in document["results"] if r["metric_id"] == "pass_over_total")
        self.assertEqual((total["status"], total["value"], total["denominator"]), ("not_measured", None, 29))
        full = robustness.rows_v1(scored())
        measured = next(r for r in full["results"] if r["metric_id"] == "pass_over_total")
        self.assertEqual((measured["status"], measured["numerator"], measured["denominator"]), ("measured", 29, 29))

    def test_every_group_behavior_and_category_is_present(self):
        document = self.rows()
        seen = {(r["grp"], r["behavior"]) for r in document["results"]}
        for group in ("baseline", "perturbation"):
            for behavior in ("answer", "clarify", "abstain"):
                self.assertIn((group, behavior), seen)
        for category in scored()["categories"]:
            self.assertIn(("category", category), seen)

    def test_no_text_names_or_free_values_leak_into_the_rows(self):
        raw = raw_fixture()
        judgments = judgments_fixture(raw)
        text = json.dumps(self.rows(raw, judgments), ensure_ascii=False)
        for forbidden in ("fixture-person-a", "UNIT TEST ONLY", "Texto sintético", "apellido"):
            self.assertNotIn(forbidden, text)

    def test_live_runs_are_not_marked_synthetic(self):
        report = scored()
        report["kind"] = "live_unverified"
        self.assertFalse(robustness.rows_v1(report)["run"]["synthetic"])

    def test_malformed_reports_are_rejected(self):
        for mutate in (lambda r: r.pop("run"), lambda r: r.pop("totals"), lambda r: r["totals"].update(total="x"),
                       lambda r: r.update(groups=[])):
            report = scored()
            mutate(report)
            with self.assertRaises(robustness.Error):
                robustness.rows_v1(report)

    def test_cli_writes_rows_next_to_the_report_and_refuses_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            report_path, output = base / "report.json", base / "rows.json"
            report_path.write_text(json.dumps(scored()), encoding="utf-8")
            status, _, stderr = cli(["rows", "--input", report_path, "--output", output])
            self.assertEqual(status, 0, stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["contract_version"], 1)
            status, _, _ = cli(["rows", "--input", report_path, "--output", report_path])
            self.assertEqual(status, 2)
            status, _, _ = cli(["rows", "--input", report_path, "--output", ROOT / "docs/evidence/notes.json"])
            self.assertEqual(status, 2)
            status, _, _ = cli(["rows", "--input", base / "missing.json", "--output", base / "other.json"])
            self.assertEqual(status, 2)

    def test_repository_rows_name_is_limited_to_generated_evidence(self):
        robustness.protect_outputs([ROOT / "docs/evidence/jup-071-template-fixed-rows.json"], [])
        with self.assertRaises(robustness.Error):
            robustness.protect_outputs([ROOT / "docs/evidence/other-rows.json"], [])


class RowsReviewTests(unittest.TestCase):
    """Regression tests for the independent pass over the rows command and unmeasured distance."""

    def blocked_report(self, failure):
        raw = raw_fixture()
        for row in raw["cases"]:
            row["failure_category"] = failure
        return scored(raw, None if failure else robustness.empty_judgments(raw))

    def test_malformed_nested_reports_fail_with_a_controlled_error_through_the_cli(self):
        mutations = (
            lambda r: r["groups"]["baseline"].update(answer=5),
            lambda r: r["groups"].update(baseline=5),
            lambda r: r["cases"][0].update(checks=None),
            lambda r: r["cases"].__setitem__(0, "x"),
            lambda r: r["run"].pop("generation"),
            lambda r: r["categories"].update(tagging="x"),
            lambda r: r.update(groups={}),
            lambda r: r.update(cases=[]),
        )
        for index, mutate in enumerate(mutations):
            report = scored()
            mutate(report)
            with self.subTest(mutation=index), tempfile.TemporaryDirectory() as folder:
                source, output = Path(folder) / "r.json", Path(folder) / "o.json"
                source.write_text(json.dumps(report), encoding="utf-8")
                status, _, stderr = cli(["rows", "--input", source, "--output", output])
                self.assertEqual(status, 2, stderr)
                self.assertTrue(stderr.startswith("JUP-071: "))
                self.assertFalse(output.exists())

    def test_inconsistent_counts_and_rates_are_rejected(self):
        mutations = (
            lambda r: r["totals"].update(fail=-3),
            lambda r: r["totals"].update(**{"pass": 40}),
            lambda r: r["totals"].update(evaluated=r["totals"]["evaluated"] + 1),
            lambda r: r["groups"]["baseline"]["answer"].update(**{"pass": 99}),
            lambda r: r["categories"]["tagging"].update(total=r["categories"]["tagging"]["total"] + 1),
            lambda r: r["totals"].update(pass_over_total=0.5),
            lambda r: r["totals"].update(pass_over_evaluated=7),
            lambda r: r["totals"].update(pass_over_total=None),
            lambda r: r["cases"][0]["checks"].update({"numbers-9": "not_run"}),
        )
        for index, mutate in enumerate(mutations):
            report = scored()
            mutate(report)
            with self.subTest(mutation=index), self.assertRaises(robustness.Error):
                robustness.rows_v1(report)

    def test_no_evaluated_cases_means_both_rates_are_not_measured(self):
        for failure in ("timeout", None):
            report = self.blocked_report(failure)
            self.assertEqual(report["totals"]["evaluated"], 0)
            rates = {r["metric_id"]: r for r in robustness.rows_v1(report)["results"] if r["grp"] == "rates"}
            for name in ("pass_over_total", "pass_over_evaluated"):
                with self.subTest(failure=failure, rate=name):
                    self.assertEqual((rates[name]["status"], rates[name]["value"]), ("not_measured", None))

    def test_provider_and_alias_travel_as_the_embedding_identity(self):
        report = scored()
        report["run"]["provider"], report["run"]["alias"] = "provider-x", "embed-1"
        run = robustness.rows_v1(report)["run"]
        self.assertEqual((run["embedding_provider"], run["embedding_alias"]), ("provider-x", "embed-1"))

    def test_an_unverified_live_model_is_not_presented_as_a_real_one(self):
        report = scored()
        report["kind"] = "live_unverified"
        report["run"]["generation"] = {"model_alias": "model-x/mini", "temperature": None}
        self.assertFalse(report["model_execution_verified"])
        self.assertIsNone(robustness.rows_v1(report)["run"]["generation_model"])
        template = robustness.rows_v1(scored())["run"]
        self.assertEqual(template["generation_model"], "plantilla-sin-modelo")

    def test_unknown_execution_kind_is_rejected(self):
        report = scored()
        report["kind"] = "other"
        with self.assertRaises(robustness.Error):
            robustness.rows_v1(report)

    def test_public_evidence_identity_and_text_fields_are_checked(self):
        base = {"id": "e1", "kind": "corpus", "distance": None}
        for bad in ([{**base, "id": ""}], [{**base, "kind": ""}], [base, dict(base)],
                    [{**base, "content": {"x": 1}}], [{**base, "source": 5}]):
            raw = raw_fixture()
            raw["cases"][0]["public_evidence"] = bad
            with self.subTest(bad=bad), self.assertRaises(robustness.Error):
                scored(raw)
        raw = raw_fixture()
        raw["cases"][0]["public_evidence"] = [{**base, "content": "texto", "source": "docs/x.md"}]
        self.assertEqual(scored(raw)["totals"]["total"], 29)

    def test_the_protocol_documents_rows_and_unmeasured_distance(self):
        text = (ROOT / "docs/validation/JUP-071-robustness.md").read_text(encoding="utf-8")
        for needle in ("rows --input", "distance", "public_evidence", "rows-v1"):
            self.assertIn(needle, text)


class RowsDashboardGuideTests(unittest.TestCase):
    """The dashboard guide (JUP-121) classifies review marks as human and reads perturbation types."""

    def test_reduced_coverage_is_a_human_mark(self):
        rows = robustness.rows_v1(scored())["results"]
        row = next(r for r in rows if r["metric_id"] == "reduced_coverage")
        self.assertEqual(row["judgment"], "human")

    def test_every_perturbation_type_has_its_case_states(self):
        report = scored()
        rows = robustness.rows_v1(report)["results"]
        for name, counts in report["perturbations"].items():
            states = {r["status"]: r for r in rows if (r["grp"], r["behavior"]) == ("perturbation_type", name)}
            with self.subTest(type=name):
                self.assertEqual(set(states), set(robustness.OUTCOMES))
                self.assertEqual(sum(r["count"] for r in states.values()), counts["total"])

    def test_malformed_perturbation_counts_are_rejected(self):
        report = scored()
        report["perturbations"][next(iter(report["perturbations"]))]["total"] += 1
        with self.assertRaises(robustness.Error):
            robustness.rows_v1(report)



class ServerProvenanceTests(unittest.TestCase):
    """The prompt hash reported by the server travels to the report and the dashboard rows, never attested."""

    HASH_A, HASH_B = "a1" * 32, "b2" * 32

    def live_raw(self, reported):
        raw = raw_fixture()
        raw["execution"]["kind"] = "live_unverified"
        config = {"commit": "abc1234", "corpus": "corpus-demo", "provider": "provider-x", "alias": "embed-1",
                  "retrieval": "top-k-4", "generation": "model-x/mini"}
        raw["execution"]["configuration"] = config
        raw["execution"]["configuration_sha256"] = robustness.digest(config)
        if reported is not None:
            raw["execution"]["collection"] = {"server_reported": reported}
        return raw

    def test_a_single_reported_prompt_hash_reaches_report_and_rows(self):
        raw = self.live_raw([{"sample_id": f"s{n}", "prompt_sha256": self.HASH_A, "attested": False} for n in range(3)])
        report = scored(raw)
        self.assertEqual(report["server_reported"], {"prompt_sha256": self.HASH_A, "state": "single", "attested": False})
        self.assertEqual(robustness.rows_v1(report)["run"]["prompt_sha256"], self.HASH_A)

    def test_mixed_or_missing_hashes_are_not_published_as_one(self):
        cases = {"mixed": [{"prompt_sha256": self.HASH_A}, {"prompt_sha256": self.HASH_B}],
                 "partial": [{"prompt_sha256": self.HASH_A}, {"sample_id": "s2"}],
                 "absent": [{"sample_id": "s1"}], "empty": []}
        for state, reported in cases.items():
            report = scored(self.live_raw(reported))
            with self.subTest(state=state):
                self.assertIsNone(report["server_reported"]["prompt_sha256"])
                self.assertEqual(report["server_reported"]["state"], "mixed" if state in ("mixed", "partial") else "absent")
                self.assertIsNone(robustness.rows_v1(report)["run"]["prompt_sha256"])

    def test_runs_without_collection_data_keep_their_reports_unchanged(self):
        report = scored()
        self.assertNotIn("server_reported", report)
        self.assertIsNone(robustness.rows_v1(report)["run"]["prompt_sha256"])

    def test_malformed_server_provenance_is_rejected(self):
        bad = ("x", {}, [1], [{"prompt_sha256": "short"}], [{"prompt_sha256": "A" * 64}], [{"prompt_sha256": 5}],
               [{"prompt_sha256": self.HASH_A, "attested": True}])
        for reported in bad:
            with self.subTest(reported=reported), self.assertRaises(robustness.Error):
                scored(self.live_raw(reported))
        raw = self.live_raw([])
        raw["execution"]["collection"] = "x"
        with self.assertRaises(robustness.Error):
            scored(raw)

    def test_rows_reject_an_invalid_report_hash(self):
        report = scored(self.live_raw([{"prompt_sha256": self.HASH_A}]))
        report["server_reported"]["prompt_sha256"] = "not-a-hash"
        with self.assertRaises(robustness.Error):
            robustness.rows_v1(report)



if __name__ == "__main__":
    unittest.main()
