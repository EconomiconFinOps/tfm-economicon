"""Coste de IA facturado frente a estimado de `tools/memory-indicators.py` (JUP-130, grupo 4)."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import date
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools" / "memory-indicators.py"
SPEC = importlib.util.spec_from_file_location("economicon_memory_indicators_ai", TOOL_PATH)
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

DASHBOARD = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_for_jup130_ai", ROOT / "tools" / "evaluation-dashboard.py")
dashboard = importlib.util.module_from_spec(DASHBOARD)
sys.modules[DASHBOARD.name] = dashboard
DASHBOARD.loader.exec_module(dashboard)

CHAT = "openrouter/z-ai/glm-5.2"
EMBEDDING = "openrouter/openai/text-embedding-3-small"
GATEWAY_KEY = "clave-gateway-de-prueba-JUP130"
PROVIDER_KEY = "clave-proveedor-de-prueba-JUP130"
START, END = date(2026, 10, 12), date(2026, 10, 21)


def chat(identifier, spend, day="2026-10-15", status="success", model=CHAT):
    return {"request_id": identifier, "call_type": "acompletion", "status": status, "spend": spend, "model": model,
            "startTime": f"{day}T10:00:00.000000Z", "metadata": {}}


def embedding(spend, day="2026-10-15", status="success", identifier="9f2c0e1a-0000-4000-8000-000000000001"):
    return {"request_id": identifier, "call_type": "aembedding", "status": status, "spend": spend, "model": EMBEDDING,
            "startTime": f"{day}T11:00:00.000000Z", "metadata": {}}


def failure(code, klass, call_type="aembedding", day="2026-10-15", model=EMBEDDING):
    return {"request_id": "f-" + code + klass, "call_type": call_type, "status": "failure", "spend": 0.0, "model": model,
            "startTime": f"{day}T12:00:00.000000Z",
            "metadata": {"error_information": {"error_code": code, "error_class": klass, "error_message": "SECRETO-DEL-PROVEEDOR"}}}


def billed(mapping):
    """Imita GET /generation: devuelve el coste facturado, None si OpenRouter responde 404."""
    def fetch(identifier):
        value = mapping[identifier]
        if value is ApiDown:
            raise tool.ApiUnavailable("conexion")
        return None if value is None else Decimal(value)
    return fetch


class ApiDown:
    pass


def row(report, metric_id, behavior="all"):
    found = [r for r in report["results"] if r["metric_id"] == metric_id and r["behavior"] == behavior]
    assert len(found) == 1, (metric_id, behavior, found)
    return found[0]


class Summarize(unittest.TestCase):
    def summary(self, rows, fetch=None, cap=200):
        return tool.summarize_spend(rows, START, END, fetch, cap)

    def test_a_chat_query_is_a_successful_acompletion_and_embeddings_stay_apart(self):
        result = self.summary([chat("gen-1", 0.5), embedding(0.25), chat("gen-2", 0.5, status="failure")])
        self.assertEqual(result.queries, 1)
        self.assertEqual(result.estimated_total, Decimal("0.5"))
        self.assertEqual(result.embeddings_estimated, Decimal("0.25"))

    def test_rows_outside_the_window_are_ignored(self):
        rows = [chat("gen-1", 1.0, day="2026-10-11"), chat("gen-2", 1.0, day="2026-10-12"), chat("gen-3", 1.0, day="2026-10-20"),
                chat("gen-4", 1.0, day="2026-10-21")]
        self.assertEqual(self.summary(rows).queries, 2)

    def test_spend_is_summed_as_exact_decimals_not_floats(self):
        rows = [chat(f"gen-{n}", 0.1) for n in range(3)]
        self.assertEqual(self.summary(rows).estimated_total, Decimal("0.3"))

    def test_the_billed_cost_comes_from_openrouter_for_confirmed_generations(self):
        rows = [chat("gen-1", 0.5), chat("gen-2", 0.25)]
        result = self.summary(rows, billed({"gen-1": "0.5", "gen-2": "0.3"}))
        self.assertEqual((result.confirmed, result.billed_total), (2, Decimal("0.8")))
        self.assertEqual(result.gap, Decimal("-0.05"))

    def test_a_404_is_unconfirmed_and_its_estimate_is_left_out_of_the_gap(self):
        rows = [chat("gen-1", 0.5), chat("gen-2", 9.0)]
        result = self.summary(rows, billed({"gen-1": "0.5", "gen-2": None}))
        self.assertEqual((result.confirmed, result.queries), (1, 2))
        self.assertEqual((result.billed_total, result.gap), (Decimal("0.5"), Decimal("0")))

    def test_a_row_without_a_generation_id_is_not_looked_up_and_is_unconfirmed(self):
        looked = []

        def fetch(identifier):
            looked.append(identifier)
            return Decimal("1")
        rows = [chat("90b5a1c0-aaaa-4bbb-8ccc-000000000000", 1.0), chat("gen-9", 1.0)]
        result = self.summary(rows, fetch)
        self.assertEqual((looked, result.confirmed, result.queries), (["gen-9"], 1, 2))

    def test_a_confirmed_zero_is_a_measured_zero_and_an_unconfirmed_zero_is_not(self):
        rows = [chat("gen-1", 0.0), chat("gen-2", 0.0)]
        result = self.summary(rows, billed({"gen-1": "0", "gen-2": None}))
        self.assertEqual((result.zero_spend_queries, result.confirmed, result.billed_total), (2, 1, Decimal("0")))

    def test_the_cap_limits_lookups_and_the_rest_lowers_the_coverage(self):
        looked = []

        def fetch(identifier):
            looked.append(identifier)
            return Decimal("1")
        rows = [chat(f"gen-{n}", 1.0, day=f"2026-10-{12 + n}") for n in range(4)]
        result = self.summary(rows, fetch, cap=2)
        self.assertEqual((looked, result.confirmed, result.queries), (["gen-0", "gen-1"], 2, 4))

    def test_when_openrouter_goes_down_midway_nothing_billed_is_reported(self):
        rows = [chat("gen-1", 0.5), chat("gen-2", 0.5)]
        result = self.summary(rows, billed({"gen-1": "0.5", "gen-2": ApiDown}))
        self.assertIsNone(result.billed_total)
        self.assertIsNone(result.gap)

    def test_without_a_fetch_the_billed_figures_are_not_measured(self):
        result = self.summary([chat("gen-1", 0.5)], None)
        self.assertEqual((result.confirmed, result.billed_total, result.gap), (0, None, None))

    def test_per_model_figures_are_kept_separately(self):
        rows = [chat("gen-1", 1.0), chat("gen-2", 3.0, model="economicon-chat-deepseek")]
        result = self.summary(rows, billed({"gen-1": "1", "gen-2": "3"}))
        self.assertEqual({m: s.queries for m, s in result.by_model.items()}, {CHAT: 1, "economicon-chat-deepseek": 1})


class Rejections(unittest.TestCase):
    def summary(self, rows):
        return tool.summarize_spend(rows, START, END, None, 200)

    def test_a_429_from_the_gateway_counts_only_as_a_gateway_rejection(self):
        result = self.summary([chat("gen-1", 1.0), failure("429", "ProxyRateLimitError")])
        self.assertEqual((result.requests, result.gateway_rejections, result.provider_errors, result.failures), (2, 1, 0, 1))

    def test_a_500_apierror_counts_only_as_a_provider_error(self):
        result = self.summary([chat("gen-1", 1.0), failure("500", "APIError")])
        self.assertEqual((result.gateway_rejections, result.provider_errors), (0, 1))

    def test_a_429_that_is_not_the_gateway_class_is_not_a_gateway_rejection(self):
        result = self.summary([failure("429", "RateLimitError")])
        self.assertEqual((result.gateway_rejections, result.provider_errors, result.failures), (0, 0, 1))

    def test_a_fourxx_apierror_is_not_a_provider_error(self):
        result = self.summary([failure("400", "APIError")])
        self.assertEqual((result.provider_errors, result.failures), (0, 1))

    def test_a_failure_without_error_information_still_counts_as_a_failure(self):
        bad = {"request_id": "x", "call_type": "aembedding", "status": "failure", "spend": 0.0, "model": EMBEDDING,
               "startTime": "2026-10-15T12:00:00Z", "metadata": None}
        result = self.summary([bad])
        self.assertEqual((result.failures, result.gateway_rejections, result.provider_errors), (1, 0, 0))

    def test_the_error_message_never_reaches_the_summary(self):
        result = self.summary([failure("500", "APIError")])
        self.assertNotIn("SECRETO-DEL-PROVEEDOR", repr(result))


class Report(unittest.TestCase):
    def report(self, rows, fetch=None, cap=200):
        return tool.ai_cost_report(rows, START, END, fetch, cap, commit=None, run_at=None)

    def test_a_full_window_reports_every_figure(self):
        rows = [chat("gen-1", 0.5), chat("gen-2", 0.25), embedding(0.001), failure("429", "ProxyRateLimitError"),
                failure("500", "APIError")]
        report, table = self.report(rows, billed({"gen-1": "0.5", "gen-2": "0.3"}))
        self.assertEqual(row(report, "queries")["value"], 2)
        self.assertEqual(row(report, "cost_estimated_total")["value"], 0.75)
        self.assertEqual(row(report, "cost_billed_total")["value"], 0.8)
        self.assertEqual(row(report, "cost_per_query")["value"], 0.4)
        self.assertEqual(row(report, "cost_gap")["value"], -0.05)
        self.assertEqual(row(report, "cost_embeddings_estimated")["value"], 0.001)
        coverage = row(report, "billed_coverage")
        self.assertEqual((coverage["numerator"], coverage["denominator"], coverage["value"]), (2, 2, 1.0))
        gateway = row(report, "gateway_rejection_rate")
        self.assertEqual((gateway["numerator"], gateway["denominator"]), (1, 5))
        provider = row(report, "provider_error_rate")
        self.assertEqual((provider["numerator"], provider["denominator"]), (1, 5))

    def test_without_openrouter_the_billed_figures_are_not_measured_and_the_estimate_stays(self):
        report, table = self.report([chat("gen-1", 0.5)], None)
        for metric in ("cost_billed_total", "cost_per_query", "cost_gap"):
            self.assertEqual(row(report, metric)["status"], "not_measured", metric)
        self.assertEqual(row(report, "cost_estimated_total")["status"], "measured")
        self.assertEqual(row(report, "billed_coverage")["value"], 0.0)
        self.assertIn("no está contrastado", table)

    def test_a_window_without_queries_has_zero_total_and_no_unit_cost(self):
        report, _ = self.report([embedding(0.01)], None)
        self.assertEqual(row(report, "queries")["value"], 0)
        self.assertEqual(row(report, "cost_estimated_total")["value"], 0.0)
        self.assertEqual(row(report, "cost_per_query")["status"], "not_measured")
        self.assertEqual(row(report, "billed_coverage")["status"], "not_measured")
        self.assertEqual(row(report, "cost_gap")["status"], "not_measured")

    def test_a_window_without_requests_leaves_both_rates_not_measured(self):
        report, _ = self.report([], None)
        self.assertEqual(row(report, "gateway_rejection_rate")["status"], "not_measured")
        self.assertEqual(row(report, "provider_error_rate")["status"], "not_measured")
        self.assertEqual(row(report, "gateway_rejection_rate")["denominator"], 0)

    def test_zero_failures_is_a_measured_zero_rate(self):
        report, _ = self.report([chat("gen-1", 0.5)], None)
        rate = row(report, "gateway_rejection_rate")
        self.assertEqual((rate["status"], rate["value"], rate["numerator"], rate["denominator"]), ("measured", 0.0, 0, 1))

    def test_each_model_has_its_own_rows(self):
        rows = [chat("gen-1", 1.0), chat("gen-2", 3.0, model="economicon-chat-deepseek")]
        report, _ = self.report(rows, billed({"gen-1": "1", "gen-2": "3"}))
        self.assertEqual(row(report, "cost_per_query", CHAT)["value"], 1.0)
        self.assertEqual(row(report, "cost_per_query", "economicon-chat-deepseek")["value"], 3.0)

    def test_the_report_passes_the_common_contract_with_type_b_and_the_group(self):
        report, _ = self.report([chat("gen-1", 0.5), failure("429", "ProxyRateLimitError")], billed({"gen-1": "0.5"}))
        run, results = dashboard.adapt_rows_v1(report)
        self.assertEqual(run["source"], "JUP-130")
        self.assertTrue(all(r["measure_type"] == "B" and r["grp"] == "ai_cost" for r in results))

    def test_neither_the_report_nor_the_table_carries_generation_ids_or_error_text(self):
        report, table = self.report([chat("gen-secreto-1", 0.5), failure("500", "APIError")], billed({"gen-secreto-1": "0.5"}))
        for text in (json.dumps(report), table):
            self.assertNotIn("gen-secreto-1", text)
            self.assertNotIn("SECRETO-DEL-PROVEEDOR", text)

    def test_the_table_declares_the_limits(self):
        _, table = self.report([chat("gen-1", 0.5)], billed({"gen-1": "0.5"}))
        for phrase in ("estimado", "facturado", "local a la máquina", "no demuestra", "ventana 2026-10-12 a 2026-10-21",
                       "python tools/memory-indicators.py ai-cost"):
            self.assertIn(phrase, table)

    def test_two_runs_are_identical_byte_for_byte(self):
        rows = [chat("gen-1", 0.5), chat("gen-2", 0.25)]
        first, second = self.report(rows, billed({"gen-1": "0.5", "gen-2": "0.3"})), self.report(rows, billed({"gen-1": "0.5", "gen-2": "0.3"}))
        self.assertEqual(json.dumps(first[0]), json.dumps(second[0]))
        self.assertEqual(first[1], second[1])

    def test_the_cost_per_query_uses_confirmed_queries_only(self):
        rows = [chat("gen-1", 1.0), chat("gen-2", 5.0)]
        report, _ = self.report(rows, billed({"gen-1": "1", "gen-2": None}))
        self.assertEqual(row(report, "cost_per_query")["value"], 1.0)
        self.assertEqual(row(report, "billed_coverage")["value"], 0.5)


class FakeServers:
    """Un gateway y un OpenRouter falsos en local; guardan las cabeceras recibidas."""

    def __init__(self, spend_rows, generations):
        self.seen = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def respond(self, code, body):
                data = json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                outer.seen.append((self.path.split("?")[0], self.headers.get("Authorization")))
                if self.path.startswith("/spend/logs"):
                    if self.headers.get("Authorization") != "Bearer " + GATEWAY_KEY:
                        return self.respond(401, {})
                    return self.respond(200, spend_rows)
                if self.path.startswith("/generation"):
                    if self.headers.get("Authorization") != "Bearer " + PROVIDER_KEY:
                        return self.respond(401, {})
                    identifier = self.path.split("id=")[1]
                    value = generations.get(identifier)
                    return self.respond(404, {}) if value is None else self.respond(200, {"data": {"total_cost": value}})
                self.respond(404, {})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class Command(unittest.TestCase):
    def run_tool(self, *args, env=None):
        environment = {k: v for k, v in os.environ.items() if k not in ("LITELLM_MASTER_KEY", "OPENROUTER_API_KEY")}
        environment.update(env or {})
        return subprocess.run([sys.executable, str(TOOL_PATH), *args], capture_output=True, text=True, encoding="utf-8",
                              cwd=ROOT, env=environment)

    def servers(self):
        rows = [chat("gen-1", 0.5), chat("gen-2", 0.25), embedding(0.001), failure("429", "ProxyRateLimitError")]
        servers = FakeServers(rows, {"gen-1": 0.5, "gen-2": 0.3})
        self.addCleanup(servers.close)
        return servers

    def base(self, servers, directory):
        return ["ai-cost", "--from", "2026-10-12", "--to", "2026-10-21", "--out", directory, "--gateway-url", servers.url,
                "--openrouter-url", servers.url, "--run-at", "2026-10-21T12:00:00Z", "--commit", "a" * 40]

    def test_it_measures_end_to_end_without_printing_either_key(self):
        servers = self.servers()
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_tool(*self.base(servers, directory),
                                   env={"LITELLM_MASTER_KEY": GATEWAY_KEY, "OPENROUTER_API_KEY": PROVIDER_KEY})
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(directory) / "JUP-130-ai-cost.rows.json").read_text("utf-8"))
            written = (Path(directory) / "JUP-130-ai-cost.rows.json").read_text("utf-8") + (Path(directory) / "JUP-130-ai-cost.md").read_text("utf-8")
            for text in (result.stdout, result.stderr, written):
                self.assertNotIn(GATEWAY_KEY, text)
                self.assertNotIn(PROVIDER_KEY, text)
                self.assertNotIn("gen-1", text)
            self.assertEqual(row(report, "cost_billed_total")["value"], 0.8)
        self.assertIn(("/spend/logs", "Bearer " + GATEWAY_KEY), servers.seen)
        self.assertEqual(sorted(path for path, _ in servers.seen if path.startswith("/generation")), ["/generation", "/generation"])

    def test_the_keys_can_come_from_files(self):
        servers = self.servers()
        with tempfile.TemporaryDirectory() as directory:
            gateway_file, provider_file = Path(directory) / "g", Path(directory) / "p"
            gateway_file.write_text(GATEWAY_KEY + "\n", encoding="utf-8")
            provider_file.write_text(PROVIDER_KEY + "\n", encoding="utf-8")
            result = self.run_tool(*self.base(servers, directory), "--gateway-key-file", str(gateway_file),
                                   "--openrouter-key-file", str(provider_file))
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(directory) / "JUP-130-ai-cost.rows.json").read_text("utf-8"))
            self.assertEqual(row(report, "cost_billed_total")["status"], "measured")

    def test_without_the_provider_key_the_billed_figures_are_not_measured_and_no_lookup_is_made(self):
        servers = self.servers()
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_tool(*self.base(servers, directory), env={"LITELLM_MASTER_KEY": GATEWAY_KEY})
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(directory) / "JUP-130-ai-cost.rows.json").read_text("utf-8"))
            self.assertEqual(row(report, "cost_billed_total")["status"], "not_measured")
            self.assertEqual(row(report, "cost_estimated_total")["status"], "measured")
            self.assertIn("OPENROUTER_API_KEY", result.stderr)
        self.assertEqual([path for path, _ in servers.seen if path.startswith("/generation")], [])

    def test_without_the_gateway_key_everything_is_not_measured(self):
        servers = self.servers()
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_tool(*self.base(servers, directory), env={"OPENROUTER_API_KEY": PROVIDER_KEY})
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(directory) / "JUP-130-ai-cost.rows.json").read_text("utf-8"))
            self.assertTrue(all(r["status"] == "not_measured" for r in report["results"]))
        self.assertEqual(servers.seen, [])

    def test_a_gateway_that_rejects_the_key_leaves_everything_not_measured(self):
        servers = self.servers()
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_tool(*self.base(servers, directory), env={"LITELLM_MASTER_KEY": "otra", "OPENROUTER_API_KEY": PROVIDER_KEY})
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(directory) / "JUP-130-ai-cost.rows.json").read_text("utf-8"))
            self.assertTrue(all(r["status"] == "not_measured" for r in report["results"]))
            self.assertNotIn("otra", result.stdout + result.stderr)

    def test_an_unreachable_gateway_leaves_everything_not_measured(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_tool("ai-cost", "--from", "2026-10-12", "--to", "2026-10-21", "--out", directory, "--gateway-url",
                                   "http://127.0.0.1:9", env={"LITELLM_MASTER_KEY": GATEWAY_KEY})
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(directory) / "JUP-130-ai-cost.rows.json").read_text("utf-8"))
            self.assertTrue(all(r["status"] == "not_measured" for r in report["results"]))

    def test_the_window_must_be_ordered_and_real(self):
        for window in (("2026-10-21", "2026-10-12"), ("2026-10-12", "2026-10-12"), ("2026-13-01", "2026-10-12")):
            result = self.run_tool("ai-cost", "--from", window[0], "--to", window[1])
            self.assertEqual(result.returncode, 2, window)

    def test_the_cap_must_be_a_positive_integer(self):
        for cap in ("0", "-1", "dos"):
            result = self.run_tool("ai-cost", "--from", "2026-10-12", "--to", "2026-10-21", "--max-generations", cap)
            self.assertEqual(result.returncode, 2, cap)


if __name__ == "__main__":
    unittest.main()
