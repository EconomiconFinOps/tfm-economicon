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
        self.assertEqual(numeric["checks"]["numbers-2"], "fail")
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
        self.assertEqual(result["checks"]["numbers-2"], "pass")
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
        row["answer"] = "Coste etiquetable: 1000 EUR. Cumplimiento por coste: 90 %."
        result = entry(scored(raw, robustness.empty_judgments(raw)), "JUP-071-002")
        self.assertEqual(result["outcome"], "fail")
        self.assertEqual(result["checks"]["numbers-1"], "pass")
        self.assertEqual(result["checks"]["numbers-2"], "fail")
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
        raw["execution"]["configuration"]["model_alias"] = "handwritten-model-name"
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
            run_info.write_text(json.dumps({"commit": "a" * 40, "corpus": {}, "provider": "fixture", "alias": "fixture", "retrieval": {}, "generation": {}}), encoding="utf-8")
            with mock.patch.dict("os.environ", {"JUP071_TEST_PASSWORD": "FIXTURE-PASSWORD"}), mock.patch.object(robustness.evaluation.urllib.request, "build_opener", return_value=transport):
                status, stdout, stderr = cli(["collect", "--base-url", "http://transport.invalid", "--tenant", "fixture-tenant", "--password-env", "JUP071_TEST_PASSWORD", "--run-info", run_info, "--output", output])
            self.assertEqual(status, 0, stderr)
            raw = json.loads(output.read_text(encoding="utf-8"))
            robustness.validate_raw(raw, SUITE, CASES)
            self.assertEqual(raw["execution"]["kind"], "live_unverified")
            self.assertFalse(raw["execution"]["model_execution_verified"])
            self.assertEqual(len(raw["cases"]), 29)
            self.assertNotIn("FIXTURE-PASSWORD", stdout + stderr + json.dumps(raw))


if __name__ == "__main__":
    unittest.main()
