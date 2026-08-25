"""Small, dependency-free benchmark for the JUP-078 LiteLLM aliases.

The script sends public synthetic cases and writes metrics only: prompts,
responses and authorization headers are never included in its JSON output.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ALIAS_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
BENCHMARK_MAX_TOKENS = 256


class RejectRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, status, message, headers, new_url):
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path("fixtures/llm-benchmark/cases.jsonl"))
    parser.add_argument(
        "--models",
        nargs="+",
        default=["economicon-chat", "economicon-chat-deepseek"],
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def endpoint(base_url: str) -> str:
    if not isinstance(base_url, str) or base_url != base_url.strip():
        raise ValueError("LITELLM_BASE_URL must be a safe absolute HTTP(S) URL")
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("LITELLM_BASE_URL must be a safe absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("LITELLM_BASE_URL must not contain credentials, query or fragment")
    try:
        parsed.port
    except ValueError as error:
        raise ValueError("LITELLM_BASE_URL contains an invalid port") from error
    clean = base_url.rstrip("/")
    suffix = "/chat/completions" if parsed.path.rstrip("/").endswith("/v1") else "/v1/chat/completions"
    return f"{clean}{suffix}"


def load_cases(path: Path) -> list[dict]:
    cases = []
    identifiers: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid benchmark JSON on line {line_number}") from error
        if not isinstance(case, dict):
            raise ValueError(f"Benchmark case on line {line_number} must be an object")
        identifier = case.get("id")
        if not isinstance(identifier, str) or not ALIAS_PATTERN.fullmatch(identifier):
            raise ValueError(f"Invalid benchmark case ID on line {line_number}")
        if identifier in identifiers:
            raise ValueError(f"Duplicate benchmark case ID on line {line_number}")
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise ValueError(f"Benchmark case on line {line_number} requires a non-empty prompt")
        terms = case.get("expected_terms")
        if not isinstance(terms, list) or not terms or any(
            not isinstance(term, str) or not term.strip() for term in terms
        ):
            raise ValueError(f"Benchmark case on line {line_number} requires expected terms")
        identifiers.add(identifier)
        cases.append(case)
    if not cases:
        raise ValueError("Benchmark case dataset must not be empty")
    return cases


def validate_models(models: list[str]) -> list[str]:
    if not models:
        raise ValueError("At least one LiteLLM model alias is required")
    if any(not isinstance(model, str) or not ALIAS_PATTERN.fullmatch(model) for model in models):
        raise ValueError("Benchmark models must be safe logical LiteLLM aliases")
    if len(models) != len(set(models)):
        raise ValueError("Benchmark model aliases must not be duplicated")
    return models


def _safe_cost(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        cost = float(value)
    except ValueError:
        return None
    return cost if math.isfinite(cost) and cost >= 0 else None


def run_case(url: str, key: str, model: str, case: dict, *, opener=None) -> dict:
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": case["prompt"]}],
            "temperature": 0,
            "max_tokens": BENCHMARK_MAX_TOKENS,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        transport = opener or urllib.request.build_opener(RejectRedirectHandler())
        with transport.open(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
            cost_header = response.headers.get("x-litellm-response-cost")
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        content = payload["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("Gateway response content must be text")
        normalized = content.casefold()
        hits = sum(term.casefold() in normalized for term in case["expected_terms"])
        usage = payload.get("usage", {})
        if not isinstance(usage, dict):
            raise ValueError("Gateway usage metadata must be an object")
        raw_cost = cost_header or usage.get("cost") or payload.get("response_cost")
        return {
            "case_id": case["id"],
            "ok": True,
            "latency_ms": latency_ms,
            "keyword_score": hits / len(case["expected_terms"]),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "resolved_model": payload.get("model"),
            "cost_usd": _safe_cost(raw_cost),
        }
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError, TypeError, IndexError) as error:
        result = {
            "case_id": case["id"],
            "ok": False,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "error_type": type(error).__name__,
        }
        if isinstance(error, urllib.error.HTTPError):
            result["status_code"] = error.code
        return result


def summarize(model: str, results: list[dict]) -> dict:
    latencies = sorted(item["latency_ms"] for item in results if item["ok"])
    p95_index = max(0, min(len(latencies) - 1, round(0.95 * len(latencies)) - 1)) if latencies else 0
    scores = [item["keyword_score"] for item in results if item["ok"]]
    costs = [item["cost_usd"] for item in results if item["ok"] and item.get("cost_usd") is not None]
    return {
        "alias": model,
        "cases": len(results),
        "successful": sum(item["ok"] for item in results),
        "mean_keyword_score": round(statistics.mean(scores), 4) if scores else 0,
        "p95_latency_ms": latencies[p95_index] if latencies else None,
        "prompt_tokens": sum(item.get("prompt_tokens") or 0 for item in results),
        "completion_tokens": sum(item.get("completion_tokens") or 0 for item in results),
        "cost_usd": round(sum(costs), 12) if costs else None,
        "results": results,
    }


def main() -> int:
    args = parse_args()
    base_url = os.getenv("LITELLM_BASE_URL", "").strip()
    key = os.getenv("LITELLM_API_KEY", "").strip()
    if not base_url or not key:
        raise SystemExit("LITELLM_BASE_URL and LITELLM_API_KEY are required")
    if "\r" in key or "\n" in key or key.startswith("sk-or-"):
        raise SystemExit("LITELLM_API_KEY must be a safe internal gateway key")

    try:
        gateway_url = endpoint(base_url)
        models = validate_models(args.models)
        cases = load_cases(args.cases)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    report = {
        "schema_version": 1,
        "content_retained": False,
        "models": [
            summarize(model, [run_case(gateway_url, key, model, case) for case in cases])
            for model in models
        ],
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0 if all(item["successful"] == item["cases"] for item in report["models"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
