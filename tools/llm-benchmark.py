"""Small, dependency-free benchmark for the JUP-078 LiteLLM aliases.

The script sends public synthetic cases and writes metrics only: prompts,
responses and authorization headers are never included in its JSON output.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path("fixtures/llm-benchmark/cases.jsonl"))
    parser.add_argument(
        "--models",
        nargs="+",
        default=["economicon-chat", "economicon-chat-candidate"],
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def endpoint(base_url: str) -> str:
    clean = base_url.rstrip("/")
    return f"{clean}/chat/completions" if clean.endswith("/v1") else f"{clean}/v1/chat/completions"


def load_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_case(url: str, key: str, model: str, case: dict) -> dict:
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": case["prompt"]}],
            "temperature": 0,
            "max_tokens": 800,
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
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        content = payload["choices"][0]["message"]["content"]
        normalized = content.casefold()
        hits = sum(term.casefold() in normalized for term in case["expected_terms"])
        usage = payload.get("usage", {})
        return {
            "case_id": case["id"],
            "ok": True,
            "latency_ms": latency_ms,
            "keyword_score": hits / len(case["expected_terms"]),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "resolved_model": payload.get("model"),
        }
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as error:
        return {
            "case_id": case["id"],
            "ok": False,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "error_type": type(error).__name__,
        }


def summarize(model: str, results: list[dict]) -> dict:
    latencies = sorted(item["latency_ms"] for item in results if item["ok"])
    p95_index = max(0, min(len(latencies) - 1, round(0.95 * len(latencies)) - 1)) if latencies else 0
    scores = [item["keyword_score"] for item in results if item["ok"]]
    return {
        "alias": model,
        "cases": len(results),
        "successful": sum(item["ok"] for item in results),
        "mean_keyword_score": round(statistics.mean(scores), 4) if scores else 0,
        "p95_latency_ms": latencies[p95_index] if latencies else None,
        "prompt_tokens": sum(item.get("prompt_tokens") or 0 for item in results),
        "completion_tokens": sum(item.get("completion_tokens") or 0 for item in results),
        "results": results,
    }


def main() -> int:
    args = parse_args()
    base_url = os.getenv("LITELLM_BASE_URL", "").strip()
    key = os.getenv("LITELLM_API_KEY", "").strip()
    if not base_url or not key:
        raise SystemExit("LITELLM_BASE_URL and LITELLM_API_KEY are required")

    cases = load_cases(args.cases)
    report = {
        "schema_version": 1,
        "content_retained": False,
        "models": [
            summarize(model, [run_case(endpoint(base_url), key, model, case) for case in cases])
            for model in args.models
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
