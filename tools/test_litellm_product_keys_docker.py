"""Opt-in real gateway acceptance, synthetic upstream only; Python stdlib runner.

JUP078_DOCKER_FAKE=1 python3 tools/test_litellm_product_keys_docker.py
Needs Docker and the pinned images locally. Owns one disposable Compose project.
"""
import json
import importlib.util
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
IMAGE = "ghcr.io/berriai/litellm@sha256:f63fb81b831b170ec16851e23c36ac5bf52ef106b271406429524a2ed730bbfd"


def main():
    if os.environ.get("JUP078_DOCKER_FAKE") != "1":
        raise SystemExit("Set JUP078_DOCKER_FAKE=1 explicitly; no real upstream is used")
    directory = Path(tempfile.mkdtemp(prefix="jup078-product-keys-"))
    project = "jup078-keys-" + secrets.token_hex(5)
    master, upstream, password = ["sk-" + secrets.token_hex(24) for _ in range(3)]
    sensitive = [master, upstream, password]
    receipt = {"project": project, "mode": "fake-upstream-no-real-spend", "checks": {}}
    checks = receipt["checks"]
    prior_logs = ""
    environment = {k: v for k, v in os.environ.items() if not k.startswith(("LITELLM_", "OPENROUTER_", "COMPOSE_"))}
    environment["COMPOSE_DISABLE_ENV_FILE"] = "1"

    def safe(value):
        for secret in sensitive:
            value = value.replace(secret, "[REDACTED]")
        return value

    def run(args, data=None, check=True, timeout=90):
        result = subprocess.run(args, input=data, text=True, capture_output=True,
                                env=environment, timeout=timeout)
        if check and result.returncode:
            (directory / "error.sanitized.txt").write_text(safe(result.stdout + result.stderr))
            raise RuntimeError("Command failed; see sanitized error receipt")
        return result

    config = run(["docker", "run", "--rm", "-i", "--network", "none", "--entrypoint", "python", IMAGE,
                  "-c", "import sys,yaml,json; print(json.dumps(yaml.safe_load(sys.stdin.read())))"],
                 (ROOT / "infra/litellm/config.example.yaml").read_text())
    config = json.loads(config.stdout)
    for model in config["model_list"]:
        model["litellm_params"]["api_base"] = "http://fake-upstream:8080/v1"
    (directory / "config.json").write_text(json.dumps(config))
    (directory / "response.json").write_text('{"answer":"SYNTHETIC_PRIVATE_RESPONSE"}')
    envfile = directory / "synthetic.env"
    envfile.write_text(f"OPENROUTER_API_KEY={upstream}\nLITELLM_MASTER_KEY={master}\nLITELLM_DATABASE_PASSWORD={password}\n")
    envfile.chmod(0o600)
    override = {"services": {
        "litellm": {"ports": [], "volumes": [str(directory / "config.json") + ":/app/economicon-config.yaml:ro"]},
        "fake-upstream": {"image": IMAGE, "entrypoint": ["python", "/fixture/server.py"],
            "environment": {"EXPECTED_KEY": upstream}, "networks": ["gateway"], "volumes": [
                str(ROOT / "apps/processor/tests/fixtures/litellm_fake_upstream.py") + ":/fixture/server.py:ro",
                str(directory / "response.json") + ":/fixture/response.json:ro"]}},
        "networks": {"gateway": {"internal": True}, "default": {"internal": True}}}
    override_path = directory / "override.yaml"
    override_text = json.dumps(override)
    override_path.write_text(override_text)
    # A dynamic loopback port prevents touching the persistent deployment.
    with envfile.open("a") as stream:
        stream.write("LITELLM_ADMIN_PORT=0\n")
    compose = ["docker", "compose", "--env-file", str(envfile), "-p", project,
               "-f", str(ROOT / "infra/litellm/docker-compose.yml"), "-f", str(override_path), "--profile", "ai"]
    forward = """import json,sys,urllib.request,urllib.error
p=json.load(sys.stdin)
r=urllib.request.Request('http://127.0.0.1:4000'+p['path'],headers={'Authorization':'Bearer '+p['key'],'Content-Type':'application/json'},data=None if p['body'] is None else json.dumps(p['body']).encode())
try: response=urllib.request.urlopen(r,timeout=20)
except urllib.error.HTTPError as e: response=e
with response: print(json.dumps({'status':response.status,'body':json.load(response)}))
"""

    def api(path, key=master, body=None):
        result = run(compose + ["exec", "-T", "litellm", "python", "-c", forward],
                     json.dumps({"path": path, "key": key, "body": body}))
        value = json.loads(result.stdout)
        return value["status"], value["body"]

    def issue(models, budget, duration="1h"):
        status, value = api("/key/generate", body={"models": models, "max_budget": budget,
            "budget_duration": "30d", "duration": duration, "rpm_limit": 60, "tpm_limit": 10000,
            "max_parallel_requests": 1})
        assert status == 200 and value.get("key"), "key creation failed"
        sensitive.append(value["key"])
        return value["key"]

    def stats():
        return json.loads(run(compose + ["exec", "-T", "fake-upstream", "python", "-c",
            "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/stats').read().decode())"]).stdout)["requests"]

    try:
        run(compose + ["up", "-d", "--pull", "never", "--wait", "--wait-timeout", "90"], timeout=100)
        for name in ("gateway", "default"):
            network = json.loads(run(["docker", "network", "inspect", project + "_" + name]).stdout)[0]
            checks[name + "_no_egress"] = network["Internal"] is True
        specification = importlib.util.spec_from_file_location("product_keys", ROOT / "tools/litellm-product-keys.py")
        product_keys = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(product_keys)

        class DockerGateway:
            def __init__(self):
                self.master = master

            def api(self, route, body=None):
                status, value = api(route, body=body)
                if value.get("key"):
                    sensitive.append(value["key"])
                if status != 200:
                    raise product_keys.ProvisionError("Synthetic gateway administration failed")
                return value

            def revoke(self, keys):
                self.api("/key/delete", {"keys": list(keys.values())})

        private_path = directory / "product-keys.private.json"
        admin = DockerGateway()
        receipt["provisioning_receipt"] = product_keys.provision(admin, private_path)
        keys = product_keys.private_json(private_path)
        backend, processor = keys["BACKEND_LITELLM_API_KEY"], keys["LITELLM_API_KEY"]
        checks["issuance_idempotent"] = product_keys.provision(admin, private_path) == receipt["provisioning_receipt"]
        checks["private_key_file"] = private_path.stat().st_mode & 0o077 == 0
        checks["separate_keys"] = backend != processor
        policies = []
        for key in (backend, processor):
            status, value = api("/key/info?key=" + key)
            info = value["info"]
            policies.append({field: info.get(field) for field in ("models", "max_budget", "budget_duration", "expires", "rpm_limit", "tpm_limit", "max_parallel_requests")})
            assert status == 200 and info["budget_duration"] == "30d" and info["expires"]
        receipt["effective_synthetic_key_policies"] = policies
        checks["aggregate_budget_10"] = sum(p["max_budget"] for p in policies) == 10
        embedding = {"model": "economicon-embedding", "input": "SYNTHETIC_PRIVATE_PROMPT", "dimensions": 1536}
        chat = {"model": "economicon-chat", "messages": [{"role": "user", "content": "SYNTHETIC_PRIVATE_PROMPT"}]}
        status, value = api("/v1/embeddings", backend, embedding)
        checks["backend_embeddings"] = status == 200 and len(value["data"][0]["embedding"]) == 1536
        checks["processor_chat"] = api("/v1/chat/completions", processor, chat)[0] == 200
        calls = stats()
        checks["upstream_secret_isolated"] = all(c["upstream_key_only"] for c in calls)
        checks["privacy_flags"] = all(c["provider"]["zdr"] and c["provider"]["data_collection"] == "deny" and not c["provider"]["allow_fallbacks"] for c in calls)
        before = len(calls)
        checks["backend_chat_denied"] = api("/v1/chat/completions", backend, chat)[0] in (401, 403)
        checks["evaluation_secondary_denied"] = api("/v1/chat/completions", processor, {**chat, "model": "economicon-chat-deepseek"})[0] in (401, 403)
        checks["denied_scope_no_upstream"] = len(stats()) == before
        expired = issue(["economicon-embedding"], 1, "1s")
        time.sleep(2)
        checks["expired_denied"] = api("/v1/embeddings", expired, embedding)[0] in (401, 403)
        checks["expired_no_upstream"] = len(stats()) == before
        checks["revoke_accepted"] = api("/key/delete", body={"keys": [backend]})[0] == 200
        checks["revoked_denied"] = api("/v1/embeddings", backend, embedding)[0] in (401, 403)
        checks["revoked_no_upstream"] = len(stats()) == before
        budget_key = issue(["economicon-embedding"], 0.0000001)
        checks["budget_initial_call"] = api("/v1/embeddings", budget_key, embedding)[0] == 200
        deadline = time.monotonic() + 70
        while time.monotonic() < deadline:
            _, value = api("/key/info?key=" + budget_key)
            if value["info"]["spend"] > 0.0000001:
                break
            time.sleep(2)
        checks["budget_accrued"] = value["info"]["spend"] > 0.0000001
        before = len(stats())
        status, value = api("/v1/embeddings", budget_key, embedding)
        checks["budget_exhausted_denied"] = status in (400, 401, 402, 403, 429) and value.get("error", {}).get("type") == "budget_exceeded"
        checks["budget_denied_no_upstream"] = len(stats()) == before
        prior_logs = run(compose + ["logs", "--no-color"], check=False).stdout
        run(compose + ["up", "-d", "--pull", "never", "--force-recreate", "--wait", "--wait-timeout", "90", "litellm-db", "litellm"], timeout=100)
        checks["processor_key_survives_restart"] = api("/v1/chat/completions", processor, chat)[0] == 200
        checks["revocation_survives_restart"] = api("/v1/embeddings", backend, embedding)[0] in (401, 403)
        assert all(checks.values()), "Acceptance checks failed: " + str([k for k, v in checks.items() if not v])
    finally:
        logs = prior_logs + run(compose + ["logs", "--no-color"], check=False).stdout
        checks["private_logs"] = not any(s in logs for s in sensitive + ["SYNTHETIC_PRIVATE_PROMPT", "SYNTHETIC_PRIVATE_RESPONSE"])
        (directory / "logs.sanitized.txt").write_text(safe(logs))
        result = run(compose + ["down", "--volumes", "--remove-orphans", "--timeout", "10"], check=False)
        receipt["cleanup_exit"] = result.returncode
        receipt["leftovers"] = {kind: run(["docker", kind, "ls", "-q", "--filter", "label=com.docker.compose.project=" + project]).stdout.split() for kind in ("container", "volume", "network")}
        checks["cleanup_complete"] = result.returncode == 0 and not any(receipt["leftovers"].values())
        envfile.unlink(missing_ok=True)
        (directory / "product-keys.private.json").unlink(missing_ok=True)
        override_path.write_text(safe(override_text))
        (directory / "receipt.json").write_text(safe(json.dumps(receipt, indent=2)))
        print("JUP078_RECEIPT=" + str(directory / "receipt.json"), flush=True)
    assert all(checks.values()), "Privacy or cleanup failed"


if __name__ == "__main__":
    main()
