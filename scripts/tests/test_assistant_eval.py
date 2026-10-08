from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


evaluation = load("economicon_assistant_eval", "tools/assistant-eval.py")
metrics = load("economicon_assistant_metrics_for_eval", "tools/assistant-metrics.py")

BANK = json.loads((ROOT / "docs/validation/JUP-069-questions.json").read_text(encoding="utf-8"))
LABELS = json.loads((ROOT / "docs/validation/JUP-022-retrieval-labels.json").read_text(encoding="utf-8"))
CATALOGUE = metrics.load_catalogue()
RULES = evaluation.load_rules()
CASES = {case["id"]: case for case in BANK["cases"]}
CRITICAL = [case["id"] for case in BANK["cases"] if case["expected"].get("numbers")]
D = Decimal

# Answers written by hand for a few cases, never taken from the tool.
GOLD = {
    "JUP-069-001": "Es un escenario simulado de agosto de 2026 en EUR: el total es 1.000 EUR (600 + 250 + 150). "
                   "Virtual Machines concentra más coste, 600 EUR, el 60 % del total.",
    "JUP-069-006": "Con un 5 % de coste unallocated el semáforo es verde, porque el límite del 5 % está incluido.",
    "JUP-069-019": "El incremento absoluto es de 150 EUR/día, pero el incremento relativo no está definido porque el baseline es 0. "
                   "Necesito un baseline útil o tratarlo como recurso nuevo sin afirmar que cumple la regla.",
    "JUP-069-023": "No tengo datos reales de tu tenant ni conexión con Azure real. Indícame una fuente autorizada o datos de coste, "
                   "y no voy a extrapolar desde ejemplos sintéticos.",
}


def judgment(case_id: str, result: str = "pass", reviewers=("lucia", "paris")) -> dict:
    case = CASES[case_id]
    return {
        f"required-{n}": [{"reviewer": name, "result": result, "note": ""} for name in reviewers]
        for n in range(1, len(case["expected"]["required"]) + 1)
    }


def raw_case(case_id: str, answer: str, retrieved=None, status: int = 201, total_ms: float = 120.0, failure=None) -> dict:
    return {
        "case": case_id, "prompt": "ignorado", "status": status, "failure_category": failure, "total_ms": total_ms,
        "answer": answer, "citations": [item["chunk_id"] for item in (retrieved or [])],
        "retrieved": retrieved or [], "requests": 1, "server_errors": 1 if (status or 0) >= 500 else 0,
    }


def fragment(chunk_id: str = "doc#1", content: str = "texto del fragmento") -> dict:
    return {"chunk_id": chunk_id, "source": "finops", "heading": "Cost Management", "distance": 0.31, "content": content}


class NumberParsingTests(unittest.TestCase):
    def test_both_decimal_conventions_and_thousand_separators(self):
        for token, value in (("1.000,50", D("1000.50")), ("1,000.50", D("1000.50")), ("1.000", D("1000")), ("10,1", D("10.1")),
                             ("0,01", D("0.01")), ("1000", D("1000")), ("2.5", D("2.5")), ("12.345.678", D("12345678")),
                             ("1,000", D("1000")), ("0.250", D("0.250"))):
            self.assertEqual(evaluation.parse_number_token(token), value, token)

    def test_a_figure_needs_a_unit_and_its_value_is_never_part_of_a_longer_number(self):
        found = {(f.value, f.unit) for f in evaluation.parse_figures("el total es 190 eur y el 90,5 % del resto, en 2026 hubo 3 servicios")}
        self.assertEqual(found, {(D("190"), "eur"), (D("90.5"), "%")})

    def test_unit_forms_are_normalised(self):
        cases = {
            "25 %": "%", "25 por ciento": "%", "25 puntos porcentuales": "%", "150 euros al día": "eur/dia",
            "150 eur/día": "eur/dia", "150 euros diarios": "eur/dia", "80 eur por mes": "eur/mes", "6 euros por pedido": "eur/pedido",
            "€ 200": "eur", "200 dólares": "usd", "200 usd": "usd", "1.000 euros": "eur",
        }
        for text, unit in cases.items():
            figures = evaluation.parse_figures(evaluation.normalize(text))
            self.assertEqual([f.unit for f in figures], [unit], text)

    def test_normalisation_folds_case_accents_and_spaces(self):
        self.assertEqual(evaluation.normalize("  El  GASTO\n de   Agosto, ÑANDÚ "), "el gasto de agosto, nandu")

    def test_sentences_do_not_split_inside_numbers(self):
        sentences = evaluation.split_sentences("El total es 1.000,50 EUR. Luego sube; y baja\nOtra línea")
        self.assertEqual(sentences, ["el total es 1.000,50 eur", "luego sube", "y baja", "otra linea"])


class NumberCheckTests(unittest.TestCase):
    TOTAL = {"label": "total", "value": 1000, "unit": "EUR", "tolerance": 0.01}

    def test_correct_figure_with_label_and_unit(self):
        self.assertTrue(evaluation.check_number("El total es 1.000 EUR.", self.TOTAL, ["total"]))
        self.assertTrue(evaluation.check_number("Total: 1000,00 euros", self.TOTAL, ["total"]))

    def test_tolerance_is_absolute_and_inclusive(self):
        spec = {"label": "unallocated", "value": 10, "unit": "%", "tolerance": 0.01}
        self.assertTrue(evaluation.check_number("El unallocated es 10,01 %", spec, ["unallocated"]))
        self.assertFalse(evaluation.check_number("El unallocated es 10,1 %", spec, ["unallocated"]))
        self.assertFalse(evaluation.check_number("El unallocated es 9,98 %", spec, ["unallocated"]))

    def test_unit_must_match_and_a_bare_number_is_not_enough(self):
        self.assertFalse(evaluation.check_number("El total es 1.000 USD.", self.TOTAL, ["total"]))
        self.assertFalse(evaluation.check_number("El total es 1.000.", self.TOTAL, ["total"]))
        self.assertFalse(evaluation.check_number("El total es 1.000 %.", self.TOTAL, ["total"]))

    def test_a_number_inside_a_longer_number_does_not_count(self):
        spec = {"label": "total", "value": 90, "unit": "EUR", "tolerance": 0.01}
        self.assertFalse(evaluation.check_number("El total es 190 EUR", spec, ["total"]))
        self.assertFalse(evaluation.check_number("El total es 90,5 EUR", spec, ["total"]))
        self.assertTrue(evaluation.check_number("El total es 90 EUR", spec, ["total"]))

    def test_a_number_glued_to_a_word_or_signed_negative_does_not_count(self):
        spec = {"label": "total", "value": 90, "unit": "EUR", "tolerance": 0.01}
        self.assertFalse(evaluation.check_number("El total es ref90 EUR.", spec, ["total"]))
        self.assertFalse(evaluation.check_number("El total es -90 EUR.", spec, ["total"]))
        self.assertFalse(evaluation.check_number("El total está entre 80-90 EUR.", spec, ["total"]))

    def test_right_number_next_to_the_wrong_label_fails(self):
        text = "Virtual Machines cuesta 1.000 EUR. El resto no se detalla."
        self.assertFalse(evaluation.check_number(text, self.TOTAL, ["total", "suma"]))

    VM = {"label": "Virtual Machines", "value": 600, "unit": "EUR", "tolerance": 0.01}

    def test_a_right_figure_under_the_label_of_another_figure_in_the_same_sentence_fails(self):
        own, other = ["virtual machines", "vm"], ["total", "suma"]
        wrong = "Virtual Machines cuesta 50 EUR y el total es 600 EUR."
        self.assertFalse(evaluation.check_number(wrong, self.VM, own, others=other))
        self.assertFalse(evaluation.check_number("El total es 600 EUR y Virtual Machines cuesta 50 EUR.", self.VM, own, others=other))

    def test_the_label_may_come_before_or_after_the_figure_when_nothing_else_claims_it(self):
        own, other = ["virtual machines", "vm"], ["total", "suma"]
        for text in ("Virtual Machines cuesta 600 EUR.", "600 EUR en Virtual Machines.", "El total es 1.000 EUR, de los cuales Virtual Machines 600 EUR.",
                     "Virtual Machines: 600 EUR y Storage: 250 EUR.", "Virtual Machines concentra más coste, 600 EUR, el 60 % del total."):
            self.assertTrue(evaluation.check_number(text, self.VM, own, others=other), text)

    def test_a_currency_word_before_the_number_and_markdown_emphasis_still_count(self):
        for text in ("El total es EUR 1.000.", "El total es USD 1.000.".replace("USD", "EUR"), "El **total** es **1.000** euros.", "El total: `1.000 EUR`."):
            self.assertTrue(evaluation.check_number(text, self.TOTAL, ["total"]), text)
        self.assertFalse(evaluation.check_number("El total es USD 1.000.", self.TOTAL, ["total"]))

    def test_label_must_be_in_the_same_sentence_as_the_figure(self):
        self.assertFalse(evaluation.check_number("El total del mes. Son 1.000 EUR en agosto.", self.TOTAL, ["total"]))

    def test_period_units_distinguish_per_day_from_per_month(self):
        spec = {"label": "delta absoluto", "value": 150, "unit": "EUR/día", "tolerance": 0.01}
        self.assertTrue(evaluation.check_number("El delta absoluto es de 150 EUR/día", spec, ["delta absoluto"]))
        self.assertTrue(evaluation.check_number("El delta absoluto son 150 euros al día", spec, ["delta absoluto"]))
        self.assertFalse(evaluation.check_number("El delta absoluto es de 150 EUR/mes", spec, ["delta absoluto"]))
        self.assertFalse(evaluation.check_number("El delta absoluto es de 150 EUR", spec, ["delta absoluto"]))

    def test_combined_edge_wrong_tolerance_and_wrong_label_in_one_answer(self):
        spec = {"label": "unallocated", "value": 5, "unit": "%", "tolerance": 0.01}
        text = "El shared es 5 %. El unallocated es 5,2 %."
        self.assertFalse(evaluation.check_number(text, spec, ["unallocated"]))


class EchoTests(unittest.TestCase):
    """A sentence that only repeats the prompt is not an answer."""

    PROMPT = "Un aumento de 100 EUR/día. ¿El presupuesto apagará mis máquinas cuando se supere?"
    ABSOLUTE = {"label": "delta absoluto", "value": 100, "unit": "EUR/día", "tolerance": 0.01}

    def test_a_figure_repeated_from_the_prompt_does_not_satisfy_the_check(self):
        echo = "Pregunta: Un aumento de 100 EUR/día."
        self.assertFalse(evaluation.check_number(echo, self.ABSOLUTE, ["aumento"], self.PROMPT))
        self.assertTrue(evaluation.check_number(echo, self.ABSOLUTE, ["aumento"]))

    def test_the_same_figure_stated_by_the_answer_still_counts(self):
        answer = "Pregunta: Un aumento de 100 EUR/día. El delta absoluto es de 100 EUR/día."
        self.assertTrue(evaluation.check_number(answer, self.ABSOLUTE, ["delta absoluto"], self.PROMPT))

    def test_a_prohibited_wording_in_a_repeated_question_is_not_a_violation(self):
        rule = {"any": [{"kind": "pattern", "pattern": r"apagara\w*\W+(\w+\W+){0,4}maquinas"}], "negation": True}
        self.assertFalse(evaluation.rule_hits(rule, "Pregunta: ¿El presupuesto apagará mis máquinas cuando se supere?", self.PROMPT))
        self.assertTrue(evaluation.rule_hits(rule, "Sí, el presupuesto apagará tus máquinas.", self.PROMPT))

    def test_a_question_repeated_as_a_statement_is_an_assertion_not_an_echo(self):
        prompt = evaluation.normalize("¿El gasto de septiembre es cero?")
        self.assertFalse(evaluation.is_echo("el gasto de septiembre es cero", prompt))
        self.assertTrue(evaluation.is_echo("¿el gasto de septiembre es cero", prompt))
        self.assertTrue(evaluation.is_echo("pregunta: ¿el gasto de septiembre es cero", prompt))

    def test_short_fragments_are_never_treated_as_echo(self):
        self.assertFalse(evaluation.is_echo("100 eur", evaluation.normalize(self.PROMPT)))
        self.assertTrue(evaluation.is_echo("un aumento de 100 eur/dia", evaluation.normalize(self.PROMPT)))


class RuleEngineTests(unittest.TestCase):
    def test_pattern_is_ignored_when_negated_right_before(self):
        rule = {"any": [{"kind": "pattern", "pattern": r"factura real"}], "negation": True}
        self.assertTrue(evaluation.rule_hits(rule, "Esto es una factura real de Azure.", ""))
        self.assertFalse(evaluation.rule_hits(rule, "Esto no es una factura real de Azure.", ""))

    def test_negation_off_keeps_a_negative_claim_as_the_violation(self):
        rule = {"any": [{"kind": "pattern", "pattern": r"no merece investigacion"}], "negation": False}
        self.assertTrue(evaluation.rule_hits(rule, "Este caso no merece investigación.", ""))

    def test_exempt_words_in_the_same_sentence_clear_the_match(self):
        rule = {"any": [{"kind": "figure", "value": 150, "unit": "EUR", "tolerance": 0.01}],
                "exempt": r"hipotetic|ejemplo", "negation": False}
        self.assertTrue(evaluation.rule_hits(rule, "Asigno 150 EUR a cada equipo.", ""))
        self.assertFalse(evaluation.rule_hits(rule, "Como ejemplo hipotético, 150 EUR a cada equipo.", ""))
        self.assertTrue(evaluation.rule_hits(rule, "Como ejemplo, queda pendiente. Asigno 150 EUR a cada equipo.", ""))

    def test_context_words_are_required_in_the_sentence_of_a_figure(self):
        rule = {"any": [{"kind": "figure", "value": 200, "unit": "EUR/mes", "tolerance": 0.01, "context": r"realizad|conseguid"}],
                "negation": False}
        self.assertTrue(evaluation.rule_hits(rule, "El ahorro realizado es 200 EUR/mes.", ""))
        self.assertFalse(evaluation.rule_hits(rule, "El ahorro identificado es 200 EUR/mes.", ""))

    def test_amount_not_in_the_prompt_flags_only_invented_amounts(self):
        rule = {"any": [{"kind": "amount_not_in_prompt"}], "negation": False}
        prompt = "Escenario con 100 EUR en demo-a."
        self.assertFalse(evaluation.rule_hits(rule, "Tu gasto de 100 EUR.", prompt))
        self.assertTrue(evaluation.rule_hits(rule, "Tu gasto de hoy es 350 EUR.", prompt))
        self.assertFalse(evaluation.rule_hits(rule, "No tengo importes.", prompt))

    def test_any_of_several_alternatives_triggers_the_rule(self):
        rule = {"any": [{"kind": "pattern", "pattern": "alfa"}, {"kind": "pattern", "pattern": "beta"}], "negation": False}
        self.assertTrue(evaluation.rule_hits(rule, "solo beta", ""))
        self.assertFalse(evaluation.rule_hits(rule, "solo gamma", ""))


class RulesFileTests(unittest.TestCase):
    def test_every_prohibited_behaviour_of_the_bank_has_a_rule(self):
        evaluation.validate_rules(RULES, BANK)
        total = sum(len(case["expected"]["forbidden"]) for case in BANK["cases"])
        self.assertEqual(sum(len(items) for items in RULES["forbidden"].values()), total)

    def test_a_missing_rule_stops_the_evaluation_naming_case_and_item(self):
        rules = copy.deepcopy(RULES)
        del rules["forbidden"]["JUP-069-005"]["2"]
        with self.assertRaises(evaluation.EvaluationError) as raised:
            evaluation.validate_rules(rules, BANK)
        self.assertIn("JUP-069-005", str(raised.exception))
        self.assertIn("2", str(raised.exception))

    def test_every_rule_catches_its_violating_examples_and_spares_the_clean_ones(self):
        for case_id, items in RULES["forbidden"].items():
            prompt = evaluation.prompt_text(CASES[case_id])
            for number, rule in items.items():
                examples = rule["examples"]
                self.assertTrue(examples["violates"] and examples["clean"], (case_id, number))
                for text in examples["violates"]:
                    with self.subTest(kind="violates", case=case_id, item=number, text=text):
                        self.assertTrue(evaluation.rule_hits(rule, text, prompt))
                for text in examples["clean"]:
                    with self.subTest(kind="clean", case=case_id, item=number, text=text):
                        self.assertFalse(evaluation.rule_hits(rule, text, prompt))

    def test_every_expected_number_has_aliases_and_the_gold_figures_are_accepted(self):
        for case_id in CRITICAL:
            numbers = CASES[case_id]["expected"]["numbers"]
            aliases = RULES["aliases"][case_id]
            self.assertEqual(len(aliases), len(numbers), case_id)
        for case_id, answer in GOLD.items():
            for position, spec in enumerate(CASES[case_id]["expected"].get("numbers", []), start=1):
                names = RULES["aliases"][case_id][str(position)]
                self.assertTrue(evaluation.check_number(answer, spec, names), (case_id, spec["label"]))

    def test_thresholds_extend_but_never_duplicate_the_catalogue_targets(self):
        catalogue_targets = {m["id"] for m in CATALOGUE["metrics"] if m.get("target")}
        for item in RULES["acceptance"]["extra"]:
            self.assertNotIn(item["metric"], catalogue_targets)
        self.assertEqual(RULES["acceptance"]["not_applicable_when_unstructured"], ["STR-1"])


class ScoreCaseTests(unittest.TestCase):
    def score(self, case_id, answer, judgments=None, provisional=False, retrieved=None, **kwargs):
        case = CASES[case_id]
        raw = raw_case(case_id, answer, retrieved, **kwargs)
        return evaluation.score_case(case, raw, judgments if judgments is not None else judgment(case_id), RULES, provisional=provisional)

    def test_a_case_passes_only_when_every_objective_and_judged_check_passes(self):
        entry, analysis = self.score("JUP-069-001", GOLD["JUP-069-001"])
        self.assertEqual(entry["outcome"], "pass", analysis)
        self.assertEqual([c["result"] for c in entry["checks"]], ["pass"] * len(entry["checks"]))
        self.assertTrue(all(c["decided_by"] == ["rule"] for c in entry["checks"] if c["class"] == "objective"))

    def test_an_untraceable_amount_without_a_unit_or_with_a_sign_blocks_a_critical_pass(self):
        for extra in (" Además gastamos 9.999 en red.", " Hay -777 € extra.", " Sobran 777 pedidos.", " Sobran -1.250,50 EUR."):
            entry, _ = self.score("JUP-069-001", GOLD["JUP-069-001"] + extra)
            self.assertEqual(entry["outcome"], "fail", extra)
            self.assertIn("untraceable", [f["origin"] for f in entry["figures"]], extra)

    def test_small_numbers_years_and_identifiers_are_not_untraceable_figures(self):
        extra = " Según el punto 2 de JUP-107 y el informe de 2026, hay 3 servicios (ADR-0002) en 12 meses."
        entry, _ = self.score("JUP-069-001", GOLD["JUP-069-001"] + extra)
        self.assertEqual(entry["outcome"], "pass", entry["figures"])

    NATURAL = (
        ("JUP-069-013", "La desviación es de 200 EUR (20 %)."), ("JUP-069-013", "El coste supera el presupuesto en 200 EUR, un 20 % más."),
        ("JUP-069-013", "Superamos el presupuesto en 200 EUR (un 20 %)."), ("JUP-069-013", "Nos pasamos en 200 EUR, es decir un 20 % sobre el presupuesto."),
        ("JUP-069-014", "Sí: el exceso previsto es de 200 EUR (un 20 % sobre el presupuesto)."), ("JUP-069-014", "Exceso previsto: 200 EUR, equivalente al 20 %."),
        ("JUP-069-016", "Aumenta 150 EUR/día, un 37,5 % sobre el baseline."), ("JUP-069-016", "El incremento absoluto es 150 EUR/día (37,5 %)."),
        ("JUP-069-005", "El coste elegible es 1.000 EUR; sin asignar: 100 EUR, el 10 %."),
        ("JUP-069-027", "Julio: 10 EUR por pedido. Agosto: 6 EUR por pedido, un 40 % menos."),
    )

    def test_natural_wordings_with_a_percentage_in_brackets_or_after_a_comma_pass_every_figure(self):
        for case_id, text in self.NATURAL:
            entry, _ = self.score(case_id, text, provisional=True)
            self.assertEqual([c["id"] for c in entry["checks"] if c["id"].startswith("numbers") and c["result"] == "fail"], [], text)

    def test_the_total_and_the_shares_a_right_answer_computes_are_not_untraceable(self):
        text = "Total: 1.000 EUR. Virtual Machines: 600 EUR (60 %). Storage: 250 EUR (25 %). Log Analytics: 150 EUR (15 %)."
        entry, _ = self.score("JUP-069-001", text)
        self.assertNotIn("untraceable", [f["origin"] for f in entry["figures"]])
        self.assertEqual(entry["outcome"], "pass")

    def test_a_difference_of_two_context_figures_is_not_untraceable(self):
        entry, _ = self.score("JUP-069-001", GOLD["JUP-069-001"] + " La diferencia entre Virtual Machines y Storage es de 350 EUR.")
        self.assertNotIn("untraceable", [f["origin"] for f in entry["figures"]])

    def test_a_share_rounded_to_one_decimal_is_still_derived_from_the_context(self):
        entry, _ = self.score("JUP-069-021", "Sobre lo implementado (150 EUR/mes) el 80 EUR/mes es el 53,3 %.")
        self.assertNotIn("untraceable", [f["origin"] for f in entry["figures"]])

    def test_a_derived_figure_must_be_the_computed_value_rounded_and_not_a_nearby_number(self):
        for text, origin in (("el 53,3 %", "context"), ("el 53,33 %", "context"), ("el 53 %", "context"), ("el 54 %", "untraceable"),
                             ("el 53,36 %", "untraceable"), ("el 53,05 %", "untraceable"), ("el 188 %", "context"), ("el 187,5 %", "context")):
            entry, _ = self.score("JUP-069-021", "Sobre lo implementado (150 EUR/mes) el 80 EUR/mes es " + text + ".")
            self.assertEqual(entry["figures"][-1]["origin"], origin, text)
        entry, _ = self.score("JUP-069-021", "La suma es de 230,04 EUR/mes.")
        self.assertEqual(entry["figures"][-1]["origin"], "untraceable")

    def test_identifiers_without_a_hyphen_are_not_amounts_but_a_loose_big_number_still_is(self):
        for extra in (" Fuente: fragmento 120 del corpus.", " Según ISO 8601.", " Ver doc:chunk:105."):
            entry, _ = self.score("JUP-069-001", GOLD["JUP-069-001"] + extra)
            self.assertEqual(entry["outcome"], "pass", extra)
        entry, _ = self.score("JUP-069-001", GOLD["JUP-069-001"] + " Sobran 4.321 pedidos.")
        self.assertEqual(entry["outcome"], "fail")

    def test_a_missing_figure_fails_the_case_even_when_reviewers_pass_it(self):
        entry, _ = self.score("JUP-069-001", "Virtual Machines es el servicio con más coste en este escenario simulado.")
        self.assertEqual(entry["outcome"], "fail")
        self.assertEqual({c["id"] for c in entry["checks"] if c["result"] == "fail"}, {"numbers-1", "numbers-2", "numbers-3"})

    def test_a_prohibited_behaviour_fails_the_case(self):
        entry, _ = self.score("JUP-069-001", GOLD["JUP-069-001"] + " Esta es una factura real de Azure.")
        self.assertEqual(entry["outcome"], "fail")
        self.assertEqual({c["id"] for c in entry["checks"] if c["result"] == "fail"}, {"forbidden-1"})

    def test_a_failed_required_point_fails_the_case(self):
        verdicts = judgment("JUP-069-001")
        verdicts["required-2"] = [{"reviewer": "lucia", "result": "fail", "note": "no señala el alcance"}, {"reviewer": "paris", "result": "fail", "note": ""}]
        entry, _ = self.score("JUP-069-001", GOLD["JUP-069-001"], verdicts)
        self.assertEqual(entry["outcome"], "fail")

    def test_a_case_without_judgements_is_not_run_and_carries_no_data(self):
        entry, analysis = self.score("JUP-069-001", GOLD["JUP-069-001"], judgments={})
        self.assertEqual(entry["outcome"], "not_run")
        self.assertEqual(entry["checks"], [])
        self.assertEqual((entry["citations"], entry["figures"], entry["latency_ms"]), ([], [], {}))
        self.assertIn("juicio", analysis["reason"])

    def test_the_same_person_written_differently_is_not_a_second_reviewer(self):
        for pair in (("Ana", "Ana" + chr(0x200b)), ("Ana", "ana"), ("ana", " ANA "), ("José", "Jose"), ("María  López", "maria lopez")):
            entry, analysis = self.score("JUP-069-001", GOLD["JUP-069-001"], judgment("JUP-069-001", reviewers=pair))
            self.assertEqual(entry["outcome"], "not_run", pair)
            self.assertIn("revisor", analysis["reason"])

    def test_a_reviewer_that_is_not_a_name_is_a_clear_error_and_not_a_crash(self):
        for name in (None, 3, ["a"]):
            bad = judgment("JUP-069-001", reviewers=("lucia",))
            bad["required-1"].append({"reviewer": name, "result": "pass", "note": ""})
            with self.assertRaises(evaluation.EvaluationError):
                self.score("JUP-069-001", GOLD["JUP-069-001"], bad)

    def test_critical_cases_need_two_different_reviewers_unless_provisional(self):
        one = judgment("JUP-069-001", reviewers=("lucia",))
        twice = judgment("JUP-069-001", reviewers=("lucia", "lucia"))
        for verdicts in (one, twice):
            entry, analysis = self.score("JUP-069-001", GOLD["JUP-069-001"], verdicts)
            self.assertEqual(entry["outcome"], "not_run", analysis)
        entry, analysis = self.score("JUP-069-001", GOLD["JUP-069-001"], one, provisional=True)
        self.assertEqual(entry["outcome"], "pass")
        self.assertTrue(analysis["single_decider"])

    def test_more_than_two_reviewers_or_an_unknown_verdict_is_an_error(self):
        three = judgment("JUP-069-023", reviewers=("a", "b", "c"))
        with self.assertRaises(evaluation.EvaluationError):
            self.score("JUP-069-023", GOLD["JUP-069-023"], three)
        odd = judgment("JUP-069-023")
        odd["required-1"][0]["result"] = "quizas"
        with self.assertRaises(evaluation.EvaluationError):
            self.score("JUP-069-023", GOLD["JUP-069-023"], odd)

    def test_non_critical_cases_accept_one_reviewer(self):
        entry, _ = self.score("JUP-069-023", GOLD["JUP-069-023"], judgment("JUP-069-023", reviewers=("lucia",)))
        self.assertEqual(entry["outcome"], "pass")

    def test_disagreement_counts_as_a_failure_and_is_reported(self):
        verdicts = judgment("JUP-069-006")
        verdicts["required-1"] = [{"reviewer": "lucia", "result": "pass", "note": ""}, {"reviewer": "paris", "result": "fail", "note": ""}]
        entry, analysis = self.score("JUP-069-006", GOLD["JUP-069-006"], verdicts)
        self.assertEqual(entry["outcome"], "fail")
        self.assertEqual(analysis["disagreements"], ["required-1"])
        self.assertEqual({tuple(c["decided_by"]) for c in entry["checks"] if c["id"] == "required-1"}, {("lucia", "paris")})

    def test_an_untraceable_figure_in_a_critical_case_blocks_the_pass(self):
        entry, _ = self.score("JUP-069-001", GOLD["JUP-069-001"] + " Además hay un ajuste de 1.234 EUR.")
        self.assertEqual(entry["outcome"], "fail")
        self.assertIn("untraceable", [f["origin"] for f in entry["figures"]])

    def test_derived_expected_figures_and_prompt_figures_are_traceable(self):
        entry, _ = self.score("JUP-069-001", GOLD["JUP-069-001"])
        self.assertNotIn("untraceable", [f["origin"] for f in entry["figures"]])
        self.assertTrue(set(f["origin"] for f in entry["figures"]) <= {"context", "question"})

    def test_a_figure_found_in_a_retrieved_fragment_is_evidence(self):
        retrieved = [fragment("doc#9", "En el ejemplo, el cargo es de 321 EUR.")]
        entry, _ = self.score("JUP-069-006", GOLD["JUP-069-006"] + " Según el documento son 321 EUR.", retrieved=retrieved)
        self.assertIn("evidence", [f["origin"] for f in entry["figures"]])

    def test_infrastructure_failure_blocks_the_case_and_is_not_a_wrong_answer(self):
        for status, category in ((500, "upstream"), (503, "upstream"), (None, "connection"), (429, "rate_limit"), (401, "authentication")):
            entry, _ = self.score("JUP-069-001", "", judgments={}, status=status, failure=category, total_ms=None)
            self.assertEqual((entry["outcome"], entry["failure_category"]), ("blocked", category))
            self.assertEqual((entry["checks"], entry["citations"], entry["figures"]), ([], [], []))

    def test_figures_are_only_those_with_a_currency_or_percent_unit(self):
        base, _ = self.score("JUP-069-006", GOLD["JUP-069-006"])
        entry, _ = self.score("JUP-069-006", GOLD["JUP-069-006"] + " En 2026 hubo 3 servicios.")
        self.assertEqual(len(base["figures"]), 2)
        self.assertEqual(len(entry["figures"]), len(base["figures"]))

    def test_latency_reports_the_total_and_attributes_the_request_to_generation(self):
        entry, _ = self.score("JUP-069-006", GOLD["JUP-069-006"], total_ms=250.4)
        self.assertEqual(entry["latency_ms"], {"embedding": 0, "retrieval": 0, "generation": 250.4, "total": 250.4})
        self.assertIs(entry["structured_ok"], True)

    def test_citations_are_the_chat_citations_and_dangling_ones_are_counted(self):
        raw = raw_case("JUP-069-006", GOLD["JUP-069-006"], [fragment("doc#1")])
        raw["citations"] = ["doc#1", "inventada#9"]
        entry, _ = evaluation.score_case(CASES["JUP-069-006"], raw, judgment("JUP-069-006"), RULES)
        self.assertEqual(entry["citations"], ["doc#1", "inventada#9"])
        self.assertEqual(entry["evidence_refs"], {"total": 2, "dangling": 1})
        self.assertEqual(entry["retrieved"][0].keys(), {"chunk_id", "source", "heading", "distance"})


class RunHeaderAndResultsTests(unittest.TestCase):
    RUN_INFO = {
        "commit": "a" * 40, "date": "2026-10-09T10:00:00Z",
        "corpus": {"sha256": "b" * 64, "documents": 5, "chunks": 60},
        "provider": "mock", "alias": "economicon-embedding",
        "retrieval": {"top_k": 4, "max_distance": None, "chunk_size": 500, "chunk_overlap": 50},
        "generation": {"model_alias": "plantilla", "temperature": None},
    }

    def full_run(self, answer="No dispongo de información suficiente para responder."):
        cases = [raw_case(case["id"], answer, [fragment(f"{case['id']}#1")]) for case in BANK["cases"]]
        judgments = {case["id"]: judgment(case["id"], "fail") for case in BANK["cases"]}
        return {"raw_version": 1, "cases": cases}, judgments

    def build(self, **kwargs):
        raw, judgments = self.full_run(**kwargs)
        return evaluation.build_results(BANK, RULES, raw, judgments, self.RUN_INFO, provisional=False)

    def test_the_results_file_is_accepted_by_the_calculator_without_changing_it(self):
        results, analysis = self.build()
        metrics.validate_results(results, BANK, LABELS, CATALOGUE)
        report = metrics.compute(results, BANK, LABELS, CATALOGUE)
        self.assertEqual(report["metrics"]["ACC-1"]["k"], 0)
        self.assertEqual(report["metrics"]["ACC-1"]["n"], 20)

    def test_results_carry_no_text_and_no_credentials(self):
        raw, judgments = self.full_run("Respuesta con texto único ZZZ-MARCA y contraseña supersecreta.")
        for case in raw["cases"]:
            case["retrieved"][0]["content"] = "FRAGMENTO-ZZZ"
        results, _ = evaluation.build_results(BANK, RULES, raw, judgments, self.RUN_INFO, provisional=False)
        dumped = json.dumps(results, ensure_ascii=False)
        for secret in ("ZZZ-MARCA", "supersecreta", "FRAGMENTO-ZZZ", "Authorization", "password"):
            self.assertNotIn(secret, dumped)
        for case in BANK["cases"][:3]:
            self.assertNotIn(case["question"], dumped)

    def test_same_inputs_give_the_same_bytes(self):
        first, _ = self.build()
        second, _ = self.build()
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(evaluation.dumps(first), evaluation.dumps(second))

    def test_availability_counts_requests_and_server_errors_of_the_run(self):
        raw, judgments = self.full_run()
        raw["cases"][0] = raw_case("JUP-069-001", "", status=500, failure="upstream", total_ms=None)
        results, _ = evaluation.build_results(BANK, RULES, raw, judgments, self.RUN_INFO, provisional=False)
        self.assertEqual(results["run"]["availability"], {"requests": 28, "server_errors": 1})
        self.assertEqual(results["cases"][0]["outcome"], "blocked")
        metrics.validate_results(results, BANK, LABELS, CATALOGUE)

    def test_a_bank_hash_mismatch_is_detected_by_the_calculator_not_hidden(self):
        results, _ = self.build()
        self.assertEqual(results["run"]["bank"]["suite_sha256"], metrics.suite_digest(BANK))

    def test_provisional_runs_list_the_single_decider_critical_cases(self):
        raw, _ = self.full_run()
        judgments = {case["id"]: judgment(case["id"], "pass", reviewers=("lucia",)) for case in BANK["cases"]}
        results, analysis = evaluation.build_results(BANK, RULES, raw, judgments, self.RUN_INFO, provisional=True)
        self.assertTrue(analysis["provisional"])
        self.assertEqual(sorted(analysis["single_decider_cases"]), sorted(CRITICAL))
        metrics.validate_results(results, BANK, LABELS, CATALOGUE)

    def test_without_provisional_mode_the_critical_cases_are_not_run(self):
        raw, _ = self.full_run()
        judgments = {case["id"]: judgment(case["id"], "pass", reviewers=("lucia",)) for case in BANK["cases"]}
        results, analysis = evaluation.build_results(BANK, RULES, raw, judgments, self.RUN_INFO, provisional=False)
        outcomes = {c["case"]: c["outcome"] for c in results["cases"]}
        self.assertTrue(all(outcomes[case_id] == "not_run" for case_id in CRITICAL))
        self.assertEqual(sorted(analysis["not_run"]), sorted(CRITICAL))


class FragmentLabelTests(unittest.TestCase):
    """Fragments are labelled with the bank source key and the section of the document they come from."""

    FINOPS = "docs/assistant-corpus/finops/azure-finops-mvp.md"
    GLOSSARY = "docs/assistant-corpus/glossary/glossary.md"
    MAP = {"doc-finops": FINOPS, "doc-glossary": GLOSSARY}

    def finops_chunk_with_heading(self, heading):
        calibration = evaluation.load_calibration()
        text = (ROOT / self.FINOPS).read_text(encoding="utf-8")
        spans = calibration.chunk_spans(text, 500, 50)
        sections = calibration.section_spans(text)
        return next(i for i, (_, s, e) in enumerate(spans) if calibration.primary_section(sections, s, e) == heading)

    def fragment_at(self, document, index):
        return {"chunk_id": f"{document}:chunk:{index}", "source": "assistant-corpus", "heading": "", "distance": 0.3, "content": "x"}

    def test_a_chunk_gets_the_bank_source_key_and_its_section(self):
        index = self.finops_chunk_with_heading("Cost Management Y Cost Analysis")
        labelled = evaluation.label_fragments([self.fragment_at("doc-finops", index)], self.MAP, 500, 50)
        self.assertEqual((labelled[0]["source"], labelled[0]["heading"]), ("finops", "Cost Management Y Cost Analysis"))

    def test_other_documents_get_their_own_name_and_unknown_ones_are_left_alone(self):
        labelled = evaluation.label_fragments([self.fragment_at("doc-glossary", 0), self.fragment_at("desconocido", 3)], self.MAP, 500, 50)
        self.assertEqual(labelled[0]["source"], "glossary")
        self.assertEqual((labelled[1]["source"], labelled[1]["heading"]), ("assistant-corpus", ""))

    def test_an_index_that_is_not_a_number_or_is_past_the_last_chunk_is_left_unlabelled(self):
        text = (ROOT / self.FINOPS).read_text(encoding="utf-8")
        past_the_end = len(evaluation.load_calibration().chunk_spans(text, 500, 50))
        for index in ("x", "-1", "", str(past_the_end)):
            labelled = evaluation.label_fragments([self.fragment_at("doc-finops", index)], self.MAP, 500, 50)
            self.assertEqual((labelled[0]["source"], labelled[0]["heading"]), ("assistant-corpus", ""), index)

    def test_a_path_outside_the_repository_corpus_is_rejected(self):
        for path in ("../../etc/hosts", "/etc/hosts", "docs/../README.md", "apps/backend/app/main.py"):
            with self.assertRaises(evaluation.EvaluationError):
                evaluation.label_fragments([self.fragment_at("x", 0)], {"x": path}, 500, 50)

    def test_the_labelling_does_not_change_the_raw_fragments(self):
        original = [self.fragment_at("doc-finops", 0)]
        snapshot = json.dumps(original)
        evaluation.label_fragments(original, self.MAP, 500, 50)
        self.assertEqual(json.dumps(original), snapshot)

    def test_labels_reach_the_results_and_make_the_retrieval_metrics_computable(self):
        index = self.finops_chunk_with_heading("Cost Management Y Cost Analysis")
        raw, judgments = RunHeaderAndResultsTests().full_run()
        raw["cases"][0]["retrieved"] = [self.fragment_at("doc-finops", index)]
        results, _ = evaluation.build_results(BANK, RULES, raw, judgments, RunHeaderAndResultsTests.RUN_INFO, provisional=False, document_map=self.MAP)
        first = results["cases"][0]["retrieved"][0]
        self.assertEqual((first["source"], first["heading"]), ("finops", "Cost Management Y Cost Analysis"))
        report = metrics.compute(results, BANK, LABELS, CATALOGUE)
        self.assertGreaterEqual(report["metrics"]["REL-1"]["k"], 1)
        self.assertGreaterEqual(report["metrics"]["REL-2"]["k"], 1)


class VerdictTests(unittest.TestCase):
    def report(self, **targets):
        metrics_block = {
            "ACC-1": {"available": True, "k": 18, "n": 20, "rate": 0.9, "ci95": [0.7, 0.97], "target": None},
            "ACC-2": {"available": True, "rate": 0.95, "target": {"comparator": ">=", "value": 0.9, "met": True}},
            "GRD-2": {"available": True, "total": 0, "target": {"comparator": "==", "value": 0, "met": True}},
            "LAT-2": {"stages": {"total": {"n": 25, "value": 800, "target": {"comparator": "<=", "value": 10000, "met": True}}}},
            "STR-1": {"available": False, "rate": None, "target": {"comparator": ">=", "value": 0.95, "met": None}},
        }
        for name, patch in targets.items():
            metrics_block[name.replace("_", "-")].update(patch)
        return {"metrics": metrics_block}

    def test_accepted_when_every_applicable_threshold_is_met(self):
        result = evaluation.verdict(self.report(), RULES)
        self.assertTrue(result["accepted"], result)
        statuses = {item["metric"]: item["status"] for item in result["thresholds"]}
        self.assertEqual(statuses["STR-1"], "not_applicable")
        self.assertEqual(statuses["ACC-1"], "met")

    def test_an_unmet_threshold_rejects_and_names_the_metric(self):
        result = evaluation.verdict(self.report(ACC_2={"target": {"comparator": ">=", "value": 0.9, "met": False}}), RULES)
        self.assertFalse(result["accepted"])
        self.assertIn("ACC-2", " ".join(result["reasons"]))

    def test_the_extra_threshold_on_answer_cases_is_applied(self):
        result = evaluation.verdict(self.report(ACC_1={"rate": 0.7, "k": 14}), RULES)
        self.assertFalse(result["accepted"])
        self.assertIn("ACC-1", " ".join(result["reasons"]))

    def test_a_required_threshold_that_cannot_be_computed_is_never_met(self):
        result = evaluation.verdict(self.report(GRD_2={"available": False, "target": {"comparator": "==", "value": 0, "met": None}}), RULES)
        self.assertFalse(result["accepted"])
        self.assertEqual({i["metric"]: i["status"] for i in result["thresholds"]}["GRD-2"], "not_available")

    def test_structured_threshold_applies_when_the_chat_returns_structured_output(self):
        report = self.report(STR_1={"available": True, "rate": 0.5, "target": {"comparator": ">=", "value": 0.95, "met": False}})
        structured = copy.deepcopy(RULES)
        structured["acceptance"]["structured_output"] = True
        self.assertFalse(evaluation.verdict(report, structured)["accepted"])

    def test_a_schema_threshold_that_cannot_be_computed_is_not_available_even_with_structured_output(self):
        report = self.report(STR_1={"available": False, "rate": None, "target": {"comparator": ">=", "value": 0.95, "met": None}})
        structured = copy.deepcopy(RULES)
        structured["acceptance"]["structured_output"] = True
        result = evaluation.verdict(report, structured)
        self.assertEqual({i["metric"]: i["status"] for i in result["thresholds"]}["STR-1"], "not_available")
        self.assertFalse(result["accepted"])

    def test_the_schema_threshold_is_not_applicable_while_the_chat_has_no_structured_output_even_if_the_contract_check_is_met(self):
        report = self.report(STR_1={"available": True, "rate": 1.0, "target": {"comparator": ">=", "value": 0.95, "met": True}})
        result = evaluation.verdict(report, RULES)
        status = {item["metric"]: item["status"] for item in result["thresholds"]}
        self.assertEqual(status["STR-1"], "not_applicable")
        self.assertNotIn("met", [status["STR-1"]])


class CollectTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        outer = self
        self.mode = {"messages": 201}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                return

            def respond(self, status, payload):
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                outer.requests.append((self.path, dict(self.headers), body))
                if self.path == "/auth/login":
                    return self.respond(200, {"access_token": "tok-123", "token_type": "bearer"})
                if self.path == "/assistant/conversations":
                    count = sum(1 for p, _, _ in outer.requests if p == "/assistant/conversations")
                    return self.respond(201, {"id": f"conv-{count}", "title": body["title"]})
                if self.path.endswith("/messages"):
                    if outer.mode["messages"] != 201:
                        return self.respond(outer.mode["messages"], {"detail": "boom"})
                    return self.respond(201, {
                        "conversation": {"id": "x"}, "user_message": {"id": "u1", "role": "user", "content": body["content"], "metadata": {}},
                        "assistant_message": {"id": "a1", "role": "assistant", "content": "respuesta", "metadata": {"citations": ["doc#1"]}},
                        "retrieved_context": [{"chunk_id": "doc#1", "source": "finops", "heading": "H", "distance": 0.3, "content": "texto"}],
                    })
                self.respond(404, {})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.inputs = {"jup": "JUP-069", "suite_version": "1.0.0", "suite_sha256": "x", "cases": [
            {"id": "JUP-069-001", "prompt": "  Prompt uno exacto\ncon salto y espacios  \n"}, {"id": "JUP-069-002", "prompt": "Prompt dos"}]}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def collect(self, **kwargs):
        return evaluation.collect_cases(self.base, "operator@example.com", "clave-de-prueba", "tenant-core", self.inputs, timeout=5, **kwargs)

    def test_each_case_uses_a_new_conversation_and_the_exact_prompt(self):
        raw = self.collect()
        sent = [body["content"] for path, _, body in self.requests if path.endswith("/messages")]
        self.assertEqual(sent, ["  Prompt uno exacto\ncon salto y espacios  \n", "Prompt dos"])
        self.assertEqual(sum(1 for p, _, _ in self.requests if p == "/assistant/conversations"), 2)
        paths = [p for p, _, _ in self.requests if p.endswith("/messages")]
        self.assertEqual(paths, ["/assistant/conversations/conv-1/messages", "/assistant/conversations/conv-2/messages"])
        self.assertEqual([c["answer"] for c in raw["cases"]], ["respuesta", "respuesta"])
        self.assertEqual(raw["cases"][0]["citations"], ["doc#1"])
        self.assertEqual(raw["cases"][0]["retrieved"][0]["distance"], 0.3)

    def test_the_paths_used_are_the_ones_the_backend_actually_serves(self):
        source = (ROOT / "apps" / "backend" / "app" / "api" / "routes" / "assistant.py").read_text(encoding="utf-8")
        self.assertIn('APIRouter(prefix="/assistant"', source)
        self.assertIn('"/conversations/{conversation_id}/messages"', source)
        self.assertRegex(source, r'@router\.post\(\s*"/conversations"')
        tool = (ROOT / "tools" / "assistant-eval.py").read_text(encoding="utf-8")
        self.assertIn('"/assistant/conversations"', tool)
        self.assertIn("/assistant/conversations/{conversation[", tool)
        auth = (ROOT / "apps" / "backend" / "app" / "api" / "routes" / "auth.py").read_text(encoding="utf-8")
        self.assertIn('@router.post("/auth/login"', auth)
        self.assertIn('"/auth/login"', tool)

    def test_nothing_from_the_expected_section_is_sent(self):
        self.collect()
        wire = json.dumps([body for _, _, body in self.requests])
        for case in BANK["cases"][:5]:
            for phrase in case["expected"]["required"] + case["expected"]["forbidden"]:
                self.assertNotIn(phrase, wire)

    def test_the_tenant_and_the_token_travel_as_headers_and_the_password_only_in_the_login(self):
        raw = self.collect()
        conv = [h for p, h, _ in self.requests if p == "/assistant/conversations"][0]
        self.assertEqual(conv.get("X-Tenant-Id"), "tenant-core")
        self.assertEqual(conv.get("Authorization"), "Bearer tok-123")
        login_bodies = [b for p, _, b in self.requests if p == "/auth/login"]
        self.assertEqual(len(login_bodies), 1)
        self.assertNotIn("clave-de-prueba", json.dumps(raw))
        self.assertNotIn("tok-123", json.dumps(raw))
        self.assertNotIn("Authorization", json.dumps(raw))

    def test_a_server_error_is_recorded_as_blocked_material_and_never_retried(self):
        self.mode["messages"] = 500
        raw = self.collect()
        self.assertEqual([c["failure_category"] for c in raw["cases"]], ["upstream", "upstream"])
        self.assertEqual(sum(1 for p, _, _ in self.requests if p.endswith("/messages")), 2)
        self.assertEqual(sum(c["server_errors"] for c in raw["cases"]), 2)

    def test_status_codes_map_to_failure_categories(self):
        for status, category in ((401, "authentication"), (403, "authentication"), (404, "request"), (422, "request"), (429, "rate_limit"), (503, "upstream")):
            self.requests.clear()
            self.mode["messages"] = status
            raw = self.collect()
            self.assertEqual(raw["cases"][0]["failure_category"], category, status)
            self.assertEqual(raw["cases"][0]["server_errors"], 1 if status >= 500 else 0, status)

    def test_no_connection_is_a_connection_failure(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.collect_cases(f"http://127.0.0.1:{port}", "a@b.c", "x", "t", self.inputs, timeout=2)

    def test_the_raw_file_cannot_be_written_inside_the_repository(self):
        inside = ROOT / "docs" / "evidence" / "crudo-prohibido.json"
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.write_private(inside, {"x": 1})
        self.assertFalse(inside.exists())
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "crudo.json"
            evaluation.write_private(target, {"x": 1})
            self.assertTrue(target.exists())


class ScriptedOpener:
    """Answers the login, the conversation and the message of each case with what the test scripts."""

    def __init__(self, messages):
        self.messages = list(messages)

    def open(self, req, timeout=None):
        url = req.full_url
        if url.endswith("/auth/login"):
            body = {"access_token": "tok"}
        elif url.endswith("/assistant/conversations"):
            body = {"id": "conv"}
        else:
            step = self.messages.pop(0)
            if isinstance(step, Exception):
                raise step
            body = step
        payload = json.dumps(body).encode()

        class Response:
            status = 201

            def read(self):
                return payload

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        return Response()


GOOD_REPLY = {"assistant_message": {"content": "ok", "metadata": {}}, "retrieved_context": []}


class MalformedReplyTests(unittest.TestCase):
    INPUTS = {"cases": [{"id": f"JUP-069-00{n}", "prompt": "p"} for n in (1, 2, 3)]}

    def collect(self, middle):
        opener = ScriptedOpener([GOOD_REPLY, middle, GOOD_REPLY])
        return evaluation.collect_cases("http://x", "u", "p", "t", self.INPUTS, opener=opener)

    def test_a_broken_reply_blocks_only_its_case_and_the_run_goes_on(self):
        import http.client
        broken = {
            "message is a list": {"assistant_message": [], "retrieved_context": []},
            "message is null": {"assistant_message": None, "retrieved_context": []},
            "metadata is a string": {"assistant_message": {"content": "x", "metadata": "m"}, "retrieved_context": []},
            "fragment without id": {"assistant_message": {"content": "x", "metadata": {}}, "retrieved_context": [None]},
            "body cut short": http.client.IncompleteRead(b"", 10),
            "bad status line": http.client.BadStatusLine("x"),
        }
        for name, middle in broken.items():
            raw = self.collect(middle)
            self.assertEqual([c["case"] for c in raw["cases"]], ["JUP-069-001", "JUP-069-002", "JUP-069-003"], name)
            self.assertIsNone(raw["cases"][0]["failure_category"], name)
            self.assertIsNotNone(raw["cases"][1]["failure_category"], name)
            self.assertIsNone(raw["cases"][2]["failure_category"], name)

    def test_a_reply_that_does_not_follow_the_contract_blocks_the_case_and_the_whole_run_still_scores(self):
        raw = self.collect({"assistant_message": [], "retrieved_context": []})
        self.assertEqual(raw["cases"][1]["failure_category"], "invalid_response")
        full = {"raw_version": 1, "cases": [raw_case(c["id"], "x", [fragment()]) for c in BANK["cases"]]}
        full["cases"][22] = dict(full["cases"][22], failure_category="invalid_response", status=None, total_ms=None, answer="", citations=[], retrieved=[])
        judgments = {"judgments_version": 1, "cases": {c["id"]: judgment(c["id"], "fail") for c in BANK["cases"]}}
        results, _ = evaluation.build_results(BANK, RULES, full, judgments, RunHeaderAndResultsTests.RUN_INFO, provisional=True)
        report = metrics.compute(results, BANK, LABELS, CATALOGUE)
        self.assertEqual(results["cases"][22]["outcome"], "blocked")
        self.assertTrue(report["metrics"]["AVL-1"]["available"])

    def test_fragments_with_the_wrong_types_block_only_their_case(self):
        bad = [{"chunk_id": 5, "source": "s", "distance": 0.1, "content": "c"}, {"chunk_id": "a", "source": "s", "distance": "abc", "content": "c"},
               {"chunk_id": "a", "source": "s", "distance": float("nan"), "content": "c"}, {"chunk_id": "a", "source": "s", "distance": 0.1, "content": None}]
        for fragment_ in bad:
            raw = self.collect({"assistant_message": {"content": "ok", "metadata": {}}, "retrieved_context": [fragment_]})
            self.assertEqual(raw["cases"][1]["failure_category"], "invalid_response", fragment_)
            self.assertIsNone(raw["cases"][2]["failure_category"])

    def test_text_that_cannot_be_written_in_utf8_blocks_only_its_case(self):
        lone = {"assistant_message": {"content": "hola " + chr(0xd800), "metadata": {}}, "retrieved_context": []}
        raw = self.collect(lone)
        self.assertEqual([c["failure_category"] for c in raw["cases"]], [None, "invalid_response", None])

    def test_a_lone_surrogate_in_any_text_of_the_reply_blocks_only_its_case(self):
        lone = chr(0xd800)
        fragment_ = {"chunk_id": "a", "source": "s", "distance": 0.1, "content": "c"}
        variants = {
            "source": {"assistant_message": {"content": "ok", "metadata": {}}, "retrieved_context": [dict(fragment_, source=lone)]},
            "chunk_id": {"assistant_message": {"content": "ok", "metadata": {}}, "retrieved_context": [dict(fragment_, chunk_id=lone)]},
            "content": {"assistant_message": {"content": "ok", "metadata": {}}, "retrieved_context": [dict(fragment_, content=lone)]},
            "citations": {"assistant_message": {"content": "ok", "metadata": {"citations": [lone]}}, "retrieved_context": []},
        }
        for name, reply in variants.items():
            raw = self.collect(reply)
            self.assertEqual([c["failure_category"] for c in raw["cases"]], [None, "invalid_response", None], name)
            evaluation.dumps(raw).encode("utf-8")

    def test_a_reply_nested_beyond_the_parser_limit_blocks_only_its_case(self):
        opener = ScriptedOpener([GOOD_REPLY, RecursionError(), GOOD_REPLY])
        raw = evaluation.collect_cases("http://x", "u", "p", "t", self.INPUTS, opener=opener)
        self.assertEqual([c["failure_category"] for c in raw["cases"]], [None, "invalid_response", None])


class CommandLineTests(unittest.TestCase):
    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = evaluation.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_score_end_to_end_writes_results_and_a_report_the_calculator_accepts(self):
        header = RunHeaderAndResultsTests.RUN_INFO
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            raw = {"raw_version": 1, "cases": [raw_case(c["id"], "No dispongo de datos.", [fragment(f"{c['id']}#1")]) for c in BANK["cases"]]}
            judgments = {"judgments_version": 1, "cases": {c["id"]: judgment(c["id"], "fail") for c in BANK["cases"]}}
            (folder / "raw.json").write_text(json.dumps(raw), encoding="utf-8")
            (folder / "judgments.json").write_text(json.dumps(judgments), encoding="utf-8")
            (folder / "run.json").write_text(json.dumps(header), encoding="utf-8")
            code, out, err = self.run_cli(["score", "--raw", str(folder / "raw.json"), "--judgments", str(folder / "judgments.json"),
                                          "--run-info", str(folder / "run.json"), "--output", str(folder / "results.json"),
                                          "--report", str(folder / "report.md"), "--report-json", str(folder / "report.json"),
                                          "--generated-at", "2026-10-09T12:00:00Z"])
            self.assertEqual(code, 0, err)
            saved = json.loads((folder / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["metrics"]["ACC-1"]["k"], 0)
            code, shown, _ = self.run_cli(["compare", str(folder / "report.json"), str(folder / "report.json")])
            self.assertEqual(code, 0)
            self.assertIn("ACC-1", shown)
            results = json.loads((folder / "results.json").read_text(encoding="utf-8"))
            metrics.validate_results(results, BANK, LABELS, CATALOGUE)
            report = (folder / "report.md").read_text(encoding="utf-8")
            for name in ("results.json", "report.md", "report.json"):
                self.assertNotIn(bytes([13]), (folder / name).read_bytes(), name)
            self.assertIn("No aceptado", report)
            self.assertNotIn("No dispongo de datos", report)
            self.assertIn("No aceptado", out)

    def test_score_refuses_to_run_with_a_missing_forbidden_rule(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            rules = copy.deepcopy(RULES)
            del rules["forbidden"]["JUP-069-001"]["1"]
            (folder / "rules.json").write_text(json.dumps(rules), encoding="utf-8")
            for name, content in (("raw.json", {"raw_version": 1, "cases": []}), ("judgments.json", {"cases": {}}), ("run.json", RunHeaderAndResultsTests.RUN_INFO)):
                (folder / name).write_text(json.dumps(content), encoding="utf-8")
            code, _, err = self.run_cli(["score", "--rules", str(folder / "rules.json"), "--raw", str(folder / "raw.json"),
                                        "--judgments", str(folder / "judgments.json"), "--run-info", str(folder / "run.json"),
                                        "--output", str(folder / "o.json"), "--report", str(folder / "r.md")])
            self.assertEqual(code, 2)
            self.assertIn("JUP-069-001", err)
            self.assertFalse((folder / "o.json").exists())

    def test_review_sheet_lists_every_point_and_stays_out_of_the_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            raw = {"raw_version": 1, "cases": [raw_case(c["id"], f"respuesta de {c['id']}", [fragment()]) for c in BANK["cases"]]}
            (folder / "raw.json").write_text(json.dumps(raw), encoding="utf-8")
            code, _, err = self.run_cli(["review-sheet", "--raw", str(folder / "raw.json"), "--output", str(folder / "hoja.md")])
            self.assertEqual(code, 0, err)
            sheet = (folder / "hoja.md").read_text(encoding="utf-8")
            for case in BANK["cases"]:
                self.assertIn(case["id"], sheet)
                self.assertIn(f"respuesta de {case['id']}", sheet)
            self.assertIn("required-1", sheet)
            code, _, err = self.run_cli(["review-sheet", "--raw", str(folder / "raw.json"), "--output", str(ROOT / "docs" / "hoja-prohibida.md")])
            self.assertEqual(code, 2)

    def test_a_malformed_run_header_names_the_field_and_not_only_the_exception_type(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            raw = {"raw_version": 1, "cases": [raw_case(c["id"], "x", [fragment()]) for c in BANK["cases"]]}
            judgments = {"judgments_version": 1, "cases": {c["id"]: judgment(c["id"], "fail") for c in BANK["cases"]}}
            run = dict(RunHeaderAndResultsTests.RUN_INFO, commit=3)
            for name, value in (("raw.json", raw), ("judgments.json", judgments), ("run.json", run)):
                (folder / name).write_text(json.dumps(value), encoding="utf-8")
            code, _, err = self.run_cli(["score", "--raw", str(folder / "raw.json"), "--judgments", str(folder / "judgments.json"),
                                        "--run-info", str(folder / "run.json"), "--output", str(folder / "r.json"), "--report", str(folder / "r.md")])
            self.assertEqual(code, 2)
            self.assertIn("run.commit", err)

    def test_the_report_says_which_latency_stages_are_not_measured(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            raw = {"raw_version": 1, "cases": [raw_case(c["id"], "No dispongo de datos.", [fragment()]) for c in BANK["cases"]]}
            judgments = {"judgments_version": 1, "cases": {c["id"]: judgment(c["id"], "fail") for c in BANK["cases"]}}
            for name, value in (("raw.json", raw), ("judgments.json", judgments), ("run.json", RunHeaderAndResultsTests.RUN_INFO)):
                (folder / name).write_text(json.dumps(value), encoding="utf-8")
            code, _, err = self.run_cli(["score", "--raw", str(folder / "raw.json"), "--judgments", str(folder / "judgments.json"),
                                        "--run-info", str(folder / "run.json"), "--output", str(folder / "r.json"), "--report", str(folder / "r.md")])
            self.assertEqual(code, 0, err)
            self.assertIn("Etapas no medidas", (folder / "r.md").read_text(encoding="utf-8"))

    def test_compare_shows_the_variation_between_runs_and_never_picks_the_best(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            paths = []
            for label, rate in (("uno", 0.70), ("dos", 0.80), ("tres", 0.75)):
                report = {"metrics": {"ACC-1": {"available": True, "k": 14, "n": 20, "rate": rate}, "ACC-2": {"available": True, "rate": 0.9}}}
                path = folder / f"{label}.json"
                path.write_text(json.dumps(report), encoding="utf-8")
                paths.append(str(path))
            code, out, _ = self.run_cli(["compare", *paths])
            self.assertEqual(code, 0)
            self.assertIn("ACC-1", out)
            self.assertIn("0.7", out)
            self.assertIn("0.8", out)
            self.assertRegex(out, r"(?i)variaci")

    def test_compare_prints_accents_even_when_the_console_is_not_utf8(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = []
            for label in ("uno", "dos"):
                path = Path(folder) / f"{label}.json"
                path.write_text(json.dumps({"metrics": {"ACC-1": {"available": True, "k": 1, "n": 2, "rate": 0.5}}}), encoding="utf-8")
                paths.append(str(path))
            env = {**os.environ, "PYTHONIOENCODING": "ascii"}
            done = subprocess.run([sys.executable, str(ROOT / "tools" / "assistant-eval.py"), "compare", *paths], env=env, capture_output=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn("variación".encode("utf-8"), done.stdout)


if __name__ == "__main__":
    unittest.main()
