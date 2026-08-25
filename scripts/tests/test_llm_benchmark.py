from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PATH = ROOT / "tools" / "llm-benchmark.py"
SPEC = importlib.util.spec_from_file_location("economicon_llm_benchmark", BENCHMARK_PATH)
assert SPEC is not None and SPEC.loader is not None
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


class Response:
    def __init__(self, payload, *, headers=None):
        self.payload = payload
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class Transport:
    def __init__(self, response=None, *, error=None):
        self.response = response
        self.error = error
        self.requests = []

    def open(self, request, *, timeout):
        self.requests.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


class BenchmarkTests(unittest.TestCase):
    def test_endpoint_normalizes_supported_gateway_paths(self):
        self.assertEqual(
            benchmark.endpoint("http://litellm:4000/v1/"),
            "http://litellm:4000/v1/chat/completions",
        )
        self.assertEqual(
            benchmark.endpoint("https://gateway.example.com"),
            "https://gateway.example.com/v1/chat/completions",
        )

    def test_endpoint_rejects_unsafe_urls(self):
        for value in (
            "file:///tmp/secrets",
            "http://user:secret@example.com/v1",
            "http://example.com/v1?token=secret",
            "http://example.com/v1#redirect",
            "http://example.com:99999/v1",
            " http://example.com/v1",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                benchmark.endpoint(value)

    def test_public_case_fixture_is_valid(self):
        cases = benchmark.load_cases(ROOT / "fixtures" / "llm-benchmark" / "cases.jsonl")

        self.assertEqual(len(cases), 5)
        self.assertEqual(len({case["id"] for case in cases}), 5)

    def test_load_cases_rejects_duplicate_or_incomplete_entries(self):
        cases = (
            [],
            [{"id": "case", "prompt": "", "expected_terms": ["value"]}],
            [{"id": "case", "prompt": "prompt", "expected_terms": []}],
            [{"id": "case", "prompt": "prompt", "expected_terms": [""]}],
            [{"id": "bad/id", "prompt": "prompt", "expected_terms": ["value"]}],
            [
                {"id": "same", "prompt": "first", "expected_terms": ["value"]},
                {"id": "same", "prompt": "second", "expected_terms": ["value"]},
            ],
        )
        for invalid in cases:
            with self.subTest(invalid=invalid):
                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary) / "cases.jsonl"
                    path.write_text(
                        "\n".join(json.dumps(case) for case in invalid), encoding="utf-8"
                    )
                    with self.assertRaises(ValueError):
                        benchmark.load_cases(path)

    def test_model_aliases_cannot_bypass_gateway_or_repeat(self):
        self.assertEqual(
            benchmark.validate_models(["economicon-chat", "economicon-chat-deepseek"]),
            ["economicon-chat", "economicon-chat-deepseek"],
        )
        for aliases in ([], ["z-ai/glm-5.2"], ["bad alias"], ["same", "same"]):
            with self.subTest(aliases=aliases), self.assertRaises(ValueError):
                benchmark.validate_models(aliases)

    def test_successful_case_retains_metrics_without_prompt_or_credentials(self):
        secret = "private-gateway-secret"
        prompt = "sensitive synthetic prompt"
        response = Response(
            {
                "choices": [{"message": {"content": "Compute costs 150 EUR"}}],
                "model": "z-ai/glm-5.2",
                "usage": {"prompt_tokens": 8, "completion_tokens": 4},
            },
            headers={"x-litellm-response-cost": "0.00425"},
        )
        transport = Transport(response)
        result = benchmark.run_case(
            "http://litellm:4000/v1/chat/completions",
            secret,
            "economicon-chat",
            {"id": "cost-total", "prompt": prompt, "expected_terms": ["150", "Compute"]},
            opener=transport,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["keyword_score"], 1)
        self.assertEqual(result["cost_usd"], 0.00425)
        self.assertEqual(result["resolved_model"], "z-ai/glm-5.2")
        self.assertNotIn(prompt, json.dumps(result))
        self.assertNotIn(secret, json.dumps(result))
        self.assertEqual(transport.requests[0][0].get_header("Authorization"), f"Bearer {secret}")

    def test_http_error_exposes_only_safe_class_and_status(self):
        error = urllib.error.HTTPError(
            "http://gateway/v1/chat/completions",
            401,
            "secret-not-for-output",
            {},
            io.BytesIO(b"private response"),
        )
        result = benchmark.run_case(
            "http://gateway/v1/chat/completions",
            "secret-key",
            "economicon-chat",
            {"id": "authentication", "prompt": "private prompt", "expected_terms": ["ok"]},
            opener=Transport(error=error),
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "HTTPError")
        self.assertEqual(result["status_code"], 401)
        self.assertNotIn("secret", json.dumps(result))
        self.assertNotIn("private", json.dumps(result))

    def test_malformed_gateway_response_fails_without_retaining_content(self):
        transport = Transport(Response({"choices": [], "usage": {}}))
        result = benchmark.run_case(
            "http://gateway/v1/chat/completions",
            "secret-key",
            "economicon-chat",
            {"id": "malformed", "prompt": "private prompt", "expected_terms": ["ok"]},
            opener=transport,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "IndexError")

    def test_redirect_handler_refuses_authenticated_redirects(self):
        handler = benchmark.RejectRedirectHandler()

        self.assertIsNone(handler.redirect_request(None, None, 302, "redirect", {}, "https://other"))

    def test_summary_counts_metrics_and_optional_cost(self):
        results = [
            {
                "case_id": "one",
                "ok": True,
                "latency_ms": 5,
                "keyword_score": 1.0,
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "cost_usd": 0.001,
            },
            {
                "case_id": "two",
                "ok": True,
                "latency_ms": 10,
                "keyword_score": 0.5,
                "prompt_tokens": 20,
                "completion_tokens": 10,
                "cost_usd": 0.002,
            },
            {"case_id": "three", "ok": False, "latency_ms": 2, "error_type": "HTTPError"},
        ]
        summary = benchmark.summarize("economicon-chat", results)

        self.assertEqual(summary["cases"], 3)
        self.assertEqual(summary["successful"], 2)
        self.assertEqual(summary["prompt_tokens"], 30)
        self.assertEqual(summary["completion_tokens"], 15)
        self.assertEqual(summary["cost_usd"], 0.003)
        self.assertEqual(summary["mean_keyword_score"], 0.75)

    def test_cost_validation_rejects_nonfinite_and_negative_values(self):
        for value in (None, True, "NaN", "inf", -1, "not-a-number"):
            with self.subTest(value=value):
                self.assertIsNone(benchmark._safe_cost(value))
        self.assertEqual(benchmark._safe_cost("0.001"), 0.001)


if __name__ == "__main__":
    unittest.main()
