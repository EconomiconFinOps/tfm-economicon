"""Opt in with JUP023_DOCKER_FAKE=1; owns and removes one disposable project.

Run from apps/processor: python -B -m pytest -p no:cacheprovider
tests/test_litellm_docker.py -q -s --tb=short. Receipts are retained in TEMP.
No dotenv is loaded; all upstreams use an internal-network synthetic service.
"""
import json
import math
import os
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import error, parse, request

import pytest
from pydantic import TypeAdapter

from app.agents.schemas import finops_response_format
from app.agents.service import AgentRuntime
from app.agents.providers import get_provider
from app.clients.litellm import ProviderError
from app.core.config import Settings
from app.embeddings.providers import get_embedding_provider
from test_agent_runtime import _valid_response


pytestmark = pytest.mark.skipif(os.environ.get("JUP023_DOCKER_FAKE") != "1",
                               reason="explicit JUP023_DOCKER_FAKE=1 required")
ROOT = Path(__file__).resolve().parents[3]
GATEWAY = "ghcr.io/berriai/litellm@sha256:f63fb81b831b170ec16851e23c36ac5bf52ef106b271406429524a2ed730bbfd"
DATABASE = "postgres:17-alpine@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24"


def log_privacy_leaks(logs, credentials):
    return {"prompt": "SYNTHETIC_PRIVATE_PROMPT" in logs,
            "response": "SYNTHETIC_PRIVATE_RESPONSE" in logs,
            "upstream_error": "SYNTHETIC_UPSTREAM_ERROR" in logs,
            "nested_error": "SYNTHETIC_NESTED_ERROR" in logs,
            "credential": any(key in logs for key in credentials)}


@pytest.fixture
def docker_gateway():
    import yaml

    directory = Path(tempfile.mkdtemp(prefix="jup023-docker-fake-"))
    project = "jup023-fake-" + secrets.token_hex(5)
    master, upstream, password = ("sk-" + secrets.token_hex(24) for _ in range(3))
    markers = ["SYNTHETIC_PRIVATE_PROMPT", "SYNTHETIC_PRIVATE_RESPONSE",
               "SYNTHETIC_UPSTREAM_ERROR", "SYNTHETIC_NESTED_ERROR"]
    sensitive = [master, upstream, password, *markers]
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    environment = {key: value for key, value in os.environ.items() if not (
        key.upper().startswith(("LITELLM_", "OPENROUTER_", "COMPOSE_", "AZURE_"))
        or key.upper() in {"DATABASE_URL", "ECONOMICON_ENV_FILE", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"}
    )}
    environment["COMPOSE_DISABLE_ENV_FILE"] = "1"
    env_file = directory / "synthetic.env"
    env_file.write_text(f"OPENROUTER_API_KEY={upstream}\nLITELLM_MASTER_KEY={master}\n"
                        f"LITELLM_DATABASE_PASSWORD={password}\nLITELLM_ADMIN_PORT={port}\n")
    config = yaml.safe_load((ROOT / "infra/litellm/config.example.yaml").read_text())
    mutation = os.environ.get("JUP023_CALLBACK_MUTATION", "none")
    if mutation not in {"none", "no_callback", "tracebacks"}:
        raise ValueError("Unsupported JUP023_CALLBACK_MUTATION")
    if mutation == "no_callback":
        assert config["litellm_settings"]["callbacks"] == ["safe_logging.safe_error_logger"]
        config["litellm_settings"]["callbacks"] = []
    for model in config["model_list"]:
        model["litellm_params"]["api_base"] = "http://fake-upstream:8080/v1"
    (directory / "config.yaml").write_text(yaml.safe_dump(config))
    response = _valid_response(answer=markers[1])
    (directory / "response.json").write_text(json.dumps(response))
    fake_script = Path(__file__).parent / "fixtures/litellm_fake_upstream.py"
    override = {
        "services": {
            "litellm": {"volumes": [f"{directory.as_posix()}/config.yaml:/app/economicon-config.yaml:ro"]},
            "fake-upstream": {"image": GATEWAY, "entrypoint": ["python", "/fixture/server.py"],
                "environment": {"EXPECTED_KEY": upstream}, "networks": ["gateway"],
                "volumes": [f"{fake_script.as_posix()}:/fixture/server.py:ro",
                            f"{directory.as_posix()}/response.json:/fixture/response.json:ro"]},
        }, "networks": {"gateway": {"internal": True}},
    }
    override_path = directory / "override.yaml"
    if mutation == "tracebacks":
        override["services"]["litellm"]["environment"] = {"LITELLM_SUPPRESS_SPEND_LOG_TRACEBACKS": "false"}
    override_path.write_text(yaml.safe_dump(override))
    compose = ["docker", "compose", "--env-file", str(env_file), "-p", project,
               "-f", str(ROOT / "infra/litellm/docker-compose.yml"), "-f", str(override_path)]
    receipt = {"project": project, "mode": "simulated-upstream-no-real-spend", "checks": {},
               "commands": [], "images": [GATEWAY, DATABASE], "mutation": mutation,
               "python": sys.executable, "pytest_argv": sys.argv,
               "test_environment": {"JUP023_DOCKER_FAKE": "1", "JUP023_CALLBACK_MUTATION": mutation}}

    def sanitize(text):
        for value in sensitive:
            text = text.replace(value, "[REDACTED]")
        return re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", text)

    def run(args, timeout=30, check=True, input=None):
        completed = subprocess.run(args, env=environment, cwd=directory, capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", timeout=timeout, input=input)
        receipt["commands"].append({"argv": sanitize(json.dumps(args)), "exit": completed.returncode})
        if check and completed.returncode:
            (directory / "command-error.txt").write_text(sanitize(completed.stdout + completed.stderr))
            raise RuntimeError("Docker command failed; see sanitized command-error.txt")
        return completed

    def api(path, key=master, body=None):
        req = request.Request(f"http://127.0.0.1:{port}{path}",
            data=None if body is None else json.dumps(body).encode(),
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            with request.build_opener(request.ProxyHandler({})).open(req, timeout=10) as result:
                return result.status, json.load(result)
        except error.HTTPError as exc:
            with exc:
                body = json.load(exc)
            # The pinned auth wrapper preserves type; SafeErrorLogger replaces message.
            category = body.get("error", {}).get("type")
            return exc.code, {"category": "budget_exceeded" if category == "budget_exceeded" else "unknown"}

    def fake(status=None):
        code = ("import json,urllib.request; "
                "r=urllib.request.Request('http://127.0.0.1:8080/" + ("control" if status else "stats") + "', "
                "data=" + (repr(json.dumps({"status": status}).encode()) if status else "None") + "); "
                "print(urllib.request.urlopen(r,timeout=5).read().decode())")
        return json.loads(run(compose + ["exec", "-T", "fake-upstream", "python", "-c", code]).stdout)

    print("JUP023_RECEIPTS=" + str(directory), flush=True)
    relay = None
    try:
        base = yaml.safe_load((ROOT / "infra/litellm/docker-compose.yml").read_text())
        assert base["services"]["litellm"]["image"] == GATEWAY
        assert base["services"]["litellm-db"]["image"] == DATABASE
        run(compose + ["config", "--quiet"])
        run(compose + ["up", "-d", "--pull", "never", "--wait", "--wait-timeout", "45"], timeout=50)
        network = json.loads(run(["docker", "network", "inspect", project + "_gateway"]).stdout)[0]
        receipt["checks"]["internal_network"] = network["Internal"] is True
        assert receipt["checks"]["internal_network"]
        receipt["published_port"] = run(compose + ["port", "litellm", "4000"], check=False).stdout.strip()
        # Docker Desktop may not publish ports on internal-only networks. Relay
        # over exec, preserving gateway responses; never attach an egress network.
        try:
            api("/health/liveliness")
        except error.URLError:
            forward = """import json,sys,urllib.request,urllib.error
p=json.load(sys.stdin)
r=urllib.request.Request('http://127.0.0.1:4000'+p['path'], data=p['body'].encode(), headers=p['headers'], method=p['method'])
try:
    response=urllib.request.urlopen(r,timeout=10)
except urllib.error.HTTPError as exc:
    response=exc
with response:
    print(json.dumps({'status':response.status,'body':response.read().decode()}))
"""
            class Relay(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def forward_request(self):
                    payload = {"path": self.path, "method": self.command,
                               "headers": {"Authorization": self.headers.get("Authorization", ""),
                                           "Content-Type": "application/json"},
                               "body": self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode()}
                    result = json.loads(run(compose + ["exec", "-T", "litellm", "python", "-c", forward],
                                            input=json.dumps(payload), timeout=15).stdout)
                    body = result["body"].encode()
                    self.send_response(result["status"])
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                do_GET = forward_request
                do_POST = forward_request

            relay = ThreadingHTTPServer(("127.0.0.1", 0), Relay)
            port = relay.server_port
            relay_thread = threading.Thread(target=relay.serve_forever, daemon=True)
            relay_thread.start()
            receipt["transport"] = "loopback HTTP relay via docker exec to real gateway"
        else:
            receipt["transport"] = "published loopback port"
        status, _ = api("/health/liveliness")
        receipt["checks"]["health_without_upstream"] = status == 200 and not fake()["requests"]
        yield {"api": api, "fake": fake, "receipt": receipt, "sensitive": sensitive,
               "url": f"http://127.0.0.1:{port}/v1", "run": run, "compose": compose}
    finally:
        if relay is not None:
            relay.shutdown()
            relay.server_close()
            relay_thread.join(timeout=5)
        try:
            logs = run(compose + ["logs", "--no-color"], check=False).stdout
            receipt["log_leaks"] = log_privacy_leaks(logs, [key for key in sensitive if key.startswith("sk-")])
            (directory / "container-logs.sanitized.txt").write_text(sanitize(logs), encoding="utf-8")
        finally:
            cleanup = run(compose + ["down", "--volumes", "--remove-orphans", "--timeout", "10"], timeout=45, check=False)
            receipt["cleanup_exit"] = cleanup.returncode
            leftovers = {}
            for kind, args in {"containers": ["ps", "-aq"], "volumes": ["volume", "ls", "-q"],
                               "networks": ["network", "ls", "-q"]}.items():
                leftovers[kind] = run(["docker", *args, "--filter", "label=com.docker.compose.project=" + project]).stdout.split()
            receipt["leftovers"] = leftovers
            receipt["cleanup_complete"] = cleanup.returncode == 0 and not any(leftovers.values())
            (directory / "receipt.json").write_text(sanitize(json.dumps(receipt, indent=2)), encoding="utf-8")
            env_file.unlink(missing_ok=True)
            override["services"]["fake-upstream"]["environment"]["EXPECTED_KEY"] = "[REGENERATE]"
            override_path.write_text(yaml.safe_dump(override))
            assert receipt["cleanup_complete"], "Owned Docker resources remain; see receipt.json"
        assert not any(receipt["log_leaks"].values()), "Gateway logs contain private sentinels; see receipt.json"


def test_real_gateway_with_simulated_upstream(docker_gateway):
    gateway = docker_gateway
    api, fake = gateway["api"], gateway["fake"]
    checks = gateway["receipt"]["checks"]
    status, issued = api("/key/generate", body={"models": ["economicon-chat", "economicon-embedding"],
        "duration": "10m", "max_budget": 1, "budget_duration": "1d", "rpm_limit": 100, "tpm_limit": 10000})
    checks["virtual_key_created"] = status == 200 and bool(issued.get("key"))
    assert checks["virtual_key_created"], "Virtual key creation failed"
    virtual = issued["key"]
    gateway["sensitive"].append(virtual)
    settings = Settings(_env_file=None, llm_provider="litellm", embedding_provider="litellm",
                        embedding_dimension=1536, litellm_api_key=virtual,
                        litellm_base_url=gateway["url"], llm_timeout_seconds=10)
    result = AgentRuntime(settings).invoke({"tenant_id": "synthetic-tenant", "source": "azure",
        "metadata": {"note": "SYNTHETIC_PRIVATE_PROMPT"}}, "running")
    checks["finops_chat"] = result["response"]["schema_version"] == "1.0" and result["response"]["answer"] == "SYNTHETIC_PRIVATE_RESPONSE"
    vector = get_embedding_provider("litellm", 1536, settings=settings).embed("SYNTHETIC_PRIVATE_PROMPT")
    checks["embeddings_1536_finite"] = len(vector) == 1536 and all(type(v) is float and math.isfinite(v) for v in vector)
    observed = fake()["requests"]
    gateway["receipt"]["successful_upstream_requests"] = observed
    privacy = {"zdr": True, "data_collection": "deny", "allow_fallbacks": False}
    checks["privacy_on_wire"] = len(observed) == 2 and observed[0]["provider"] == {
        **privacy, "only": ["deepinfra/fp4"], "require_parameters": True,
    } and observed[1]["provider"] == {**privacy, "max_price": {"prompt": 0.02}}
    checks["strict_schema_on_wire"] = observed[0]["response_format"] == finops_response_format()
    checks["model_controls_on_wire"] = (
        observed[0]["model"] == "z-ai/glm-5.2"
        and observed[0]["reasoning"] == {"enabled": False}
        and observed[0]["max_tokens"] == 800
        and observed[1]["model"] == "openai/text-embedding-3-small"
        and observed[1]["dimensions"] == 1536
        and observed[1]["reasoning"] is None
    )
    checks["upstream_key_isolation"] = all(item["upstream_key_only"] for item in observed)
    chat_body = {"model": "economicon-chat-deepseek", "messages": [{"role": "user", "content": "synthetic"}]}
    denied, _ = api("/v1/chat/completions", key=virtual, body=chat_body)
    chat_body["model"] = "economicon-chat"
    invalid_key = "sk-" + secrets.token_hex(24)
    gateway["sensitive"].append(invalid_key)
    unauthenticated, _ = api("/v1/chat/completions", key=invalid_key, body=chat_body)
    checks["denied_alias_and_auth"] = denied in {401, 403} and unauthenticated in {401, 403} and len(fake()["requests"]) == 2
    gateway["receipt"]["denied_statuses"] = [denied, unauthenticated]
    for status in (429, 503):
        fake(status)
        try:
            get_provider("litellm", settings=settings).invoke("SYNTHETIC_PRIVATE_PROMPT", response_format=finops_response_format())
        except ProviderError as exc:
            gateway["receipt"][f"adapter_error_{status}"] = exc.category
        else:
            checks[f"terminal_{status}"] = False
        requests = fake()["requests"]
        gateway["receipt"][f"upstream_attempts_{status}"] = len(requests)
        checks[f"three_attempts_{status}"] = len(requests) == 3
    fake(200)
    sql = 'SELECT COALESCE(json_agg(t), \'[]\'::json)::text FROM "LiteLLM_SpendLogs" t;'
    def read_spend():
        return gateway["run"](gateway["compose"] + ["exec", "-T", "litellm-db", "psql", "-U", "litellm", "-d", "litellm", "-At", "-c", sql], check=False)

    deadline = time.monotonic() + 30
    while True:
        spend = read_spend()
        if spend.returncode or len(json.loads(spend.stdout)) >= 10 or time.monotonic() >= deadline:
            break
        time.sleep(0.5)
    if spend.returncode == 0:
        rows = json.loads(spend.stdout)
        gateway["receipt"]["spend_rows"] = len(rows)
        checks["spend_has_records"] = bool(rows)
        checks["spend_content_private"] = not any(value in spend.stdout for value in gateway["sensitive"])
        gateway["receipt"]["spend_fields"] = sorted(rows[0]) if rows else []
        # Inspect the complete rows for leaks above; retain only technical fields.
        summaries = []
        for row in rows:
            metadata = row.get("metadata") or {}
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            info = metadata.get("error_information") or {}
            summaries.append({
                **{field: row.get(field) for field in (
                    "request_id", "model", "model_group", "startTime", "endTime",
                    "request_duration_ms", "prompt_tokens", "completion_tokens", "total_tokens", "spend",
                )},
                "status": row.get("status") or metadata.get("status"),
                "error_code": str(info.get("error_code") or ""),
                "error_class": info.get("error_class"),
            })
        gateway["receipt"]["spend_row_metadata"] = summaries
        failures = [row for row in summaries if row["status"] == "failure"]
        expected_codes = Counter({"429": 3, "503": 3})
        expected_codes.update(map(str, (denied, unauthenticated)))
        checks["all_failure_rows_preserved"] = Counter(row["error_code"] for row in failures) == expected_codes
        checks["failure_identity_preserved"] = len(failures) == 8 and all(
            row["request_id"] and (row["model"] or row["model_group"]) and row["error_class"]
            for row in failures
        ) and len({row["request_id"] for row in summaries}) == len(summaries)
        timestamp = TypeAdapter(datetime)
        checks["failure_timing_preserved"] = all(
            row["startTime"] and row["endTime"]
            and timestamp.validate_python(row["endTime"]) >= timestamp.validate_python(row["startTime"])
            and type(row["request_duration_ms"]) in {int, float}
            and math.isfinite(row["request_duration_ms"]) and row["request_duration_ms"] >= 0
            for row in failures
        )
        successes = [row for row in summaries if row["status"] == "success"]
        checks["successful_usage_preserved"] = Counter(
            (row["prompt_tokens"], row["completion_tokens"], row["total_tokens"]) for row in successes
        ) == Counter({(5, 10, 15): 1, (12, 0, 12): 1})
        expected_embedding_cost = Decimal("0.000000240")
        checks["embedding_spend_positive"] = any(
            row["prompt_tokens"] == 12 and row["spend"] is not None
            and abs(Decimal(str(row["spend"])) - expected_embedding_cost) <= Decimal("1e-12")
            for row in successes
        )
        checks["available_numeric_metadata_valid"] = all(
            value is None or (type(value) in {int, float} and math.isfinite(value) and value >= 0)
            for row in summaries for field in ("prompt_tokens", "completion_tokens", "total_tokens", "spend")
            for value in [row[field]]
        )
        gateway["receipt"]["failure_cost_interpretation"] = (
            "Upstream 429/503 supplies no usage or billed cost. Recorded spend is gateway metadata; "
            "zero or missing values do not prove zero upstream charges. Actual billed cost remains unknown."
        )
    else:
        gateway["receipt"]["spend_inspection"] = "unavailable"
        checks["spend_inspection_succeeded"] = False

    # Exhaust an embedding-only key through real gateway accounting, never seeded spend.
    cap = Decimal("0.000000360")
    status, issued = api("/key/generate", body={"models": ["economicon-embedding"],
        "duration": "10m", "max_budget": float(cap), "max_parallel_requests": 1})
    assert status == 200 and issued.get("key"), "Embedding budget key creation failed"
    budget_key = issued["key"]
    gateway["sensitive"].append(budget_key)
    key_path = "/key/info?key=" + parse.quote(budget_key)
    status, initial = api(key_path)
    checks["embedding_budget_initially_zero"] = status == 200 and initial["info"]["spend"] == 0 and Decimal(str(initial["info"]["max_budget"])) == cap
    embedding_body = {"model": "economicon-embedding", "input": "SYNTHETIC_PRIVATE_PROMPT", "dimensions": 1536}
    outcomes = [api("/v1/embeddings", key=budget_key, body=embedding_body)[0] for _ in range(2)]
    checks["embedding_budget_calls_succeed"] = outcomes == [200, 200] and len(fake()["requests"]) == 2
    target = Decimal("0.000000480")
    deadline = time.monotonic() + 30
    observations = []
    while True:
        status, info = api(key_path)
        accrued = Decimal(str(info["info"]["spend"])) if status == 200 else Decimal("-1")
        spend = read_spend()
        budget_rows = json.loads(spend.stdout) if spend.returncode == 0 else []
        observations.append(float(accrued))
        if (abs(accrued-target) <= Decimal("1e-12") and len(budget_rows) >= 12) or time.monotonic() >= deadline:
            break
        time.sleep(0.5)
    checks["embedding_virtual_spend_accrued"] = abs(accrued-target) <= Decimal("1e-12") and accrued > cap
    before = len(fake()["requests"])
    denied, reason = api("/v1/embeddings", key=budget_key, body=embedding_body)
    after = len(fake()["requests"])
    checks["embedding_budget_denied_before_upstream"] = denied in {400, 401, 402, 403, 429} and reason.get("category") == "budget_exceeded" and before == after == 2
    checks["embedding_budget_spend_private"] = not any(value in spend.stdout for value in gateway["sensitive"])
    gateway["receipt"]["embedding_budget"] = {
        "cap_usd": float(cap), "expected_per_call_usd": 0.000000240,
        "call_statuses": outcomes, "counter_observations_usd": observations,
        "actual_counter_usd": float(accrued), "denial_status": denied,
        "denial_category": reason.get("category", "unknown"),
        "pre_denial_limits": {field: info["info"].get(field) for field in (
            "models", "max_budget", "spend", "max_parallel_requests", "rpm_limit", "tpm_limit", "expires",
        )},
        "upstream_before_denial": before, "upstream_after_denial": after,
        "spend_rows_after_calls": len(budget_rows),
    }
    assert all(checks.values()), "Measured gateway checks failed; see receipt.json"
