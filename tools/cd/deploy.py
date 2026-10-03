"""JUP-052. Private, disposable development CD; no third-party dependencies."""
import argparse
import contextlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import uuid

REPOSITORY = "EconomiconFinOps/tfm-economicon"
REMOTE = f"https://github.com/{REPOSITORY}.git"
SHA = re.compile(r"^[0-9a-f]{40}$")
PORTS = {"COCKROACH_SQL_PORT": 0, "COCKROACH_HTTP_PORT": 1,
         "RABBITMQ_PORT": 2, "RABBITMQ_MANAGEMENT_PORT": 3, "PGVECTOR_PORT": 4,
         "API_HOST_PORT": 5, "PROCESSOR_HOST_PORT": 6,
         "AZURE_COST_API_HOST_PORT": 7, "FRONTEND_HOST_PORT": 8,
         "PROMETHEUS_PORT": 9, "GRAFANA_PORT": 10}


def run(args, cwd=None, capture=False, timeout=1200, env=None):
    # Never include subprocess output in exceptions: Compose can contain secrets.
    result = subprocess.run(args, cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.PIPE if capture else None, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed (exit {result.returncode})")
    return result.stdout if capture else None


def api(path):
    request = urllib.request.Request(f"https://api.github.com/repos/{REPOSITORY}/{path}",
                                     headers={"Accept": "application/vnd.github+json",
                                              "User-Agent": "economicon-jup052"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def eligible_run(runs, head):
    # Latest attempt/run wins: never fall back to an older green deployment.
    if not runs:
        return None
    latest = max(runs, key=lambda r: (r["id"], r.get("run_attempt", 1)))
    if (latest.get("head_sha") == head and latest.get("head_branch") == "develop"
            and latest.get("event") in {"push", "workflow_dispatch"}
            and latest.get("status") == "completed" and latest.get("conclusion") == "success"
            and latest.get("head_repository", {}).get("full_name") == REPOSITORY):
        return latest
    return None


def atomic_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def init(root, port_base):
    if not 1024 <= port_base <= 65424:
        raise ValueError("Port base must leave room for both eleven-port slots")
    if (root / "config.json").exists() or (root / "secrets.json").exists():
        raise ValueError("Already initialized; existing secrets must be preserved")
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(root, 0o700)
    values = {name: secrets.token_hex(24) for name in (
        "AUTH_SECRET_KEY", "POSTGRES_PASSWORD", "RABBITMQ_DEFAULT_PASS",
        "RABBITMQ_ERLANG_COOKIE", "GRAFANA_ADMIN_PASSWORD", "DEMO_PASSWORD")}
    values.update(RUNTIME_ENVIRONMENT="development", ALLOW_INSECURE_LOCAL_DATABASE="true",
                  DEMO_SEED_ENABLED="true", RABBITMQ_DEFAULT_USER="economicon",
                  DATABASE_URL="postgresql://root@cockroachdb:26257/defaultdb?sslmode=disable",
                  VECTOR_DATABASE_URL=f"postgresql://postgres:{values['POSTGRES_PASSWORD']}@postgres-pgvector:5432/embeddings",
                  RABBITMQ_URL=f"amqp://economicon:{values['RABBITMQ_DEFAULT_PASS']}@rabbitmq:5672/",
                  EMBEDDING_PROVIDER="mock", LLM_PROVIDER="mock", AI_EXECUTION_MODE="development")
    atomic_json(root / "secrets.json", values)
    atomic_json(root / "config.json", {"port_base": port_base})


def compose(release, *args, capture=False):
    return run(["docker", "compose", "--project-directory", str(release),
                "--env-file", str(release / ".env"), "-f", str(release / "compose.json"),
                *args], cwd=release, capture=capture)


def prepare(root, source, sha, slot):
    if not SHA.fullmatch(sha):
        raise ValueError("Expected full lowercase commit SHA")
    release = root / "releases" / sha
    if release.exists():
        # Retrying a failed SHA uses its original immutable source/config.
        if json.loads((release / "release.json").read_text())["slot"] != slot:
            raise ValueError("Stored release slot is occupied; use rollback for a previous release")
        return release
    temporary = root / "releases" / (sha + ".preparing")
    temporary.mkdir(parents=True, mode=0o700)
    try:
        shutil.copytree(source, temporary, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".git", "node_modules", ".venv", ".env*", "__pycache__"))
        base = json.loads((root / "config.json").read_text())["port_base"] + slot * 100
        values = json.loads((root / "secrets.json").read_text())
        values.update({name: str(base + offset) for name, offset in PORTS.items()})
        values.update(COMPOSE_PROJECT_NAME=f"economicon-cd-{sha[:12]}",
                      VITE_API_BASE_URL=f"http://127.0.0.1:{base + 5}",
                      CORS_ALLOWED_ORIGINS=json.dumps([f"http://127.0.0.1:{base + 8}", f"http://localhost:{base + 8}"], separators=(",", ":")))
        (temporary / ".env").write_text("".join(f"{k}='{v}'\n" for k, v in values.items()))
        os.chmod(temporary / ".env", 0o600)
        # Render silently, then enforce private ports regardless of base Compose defaults.
        config = json.loads(run(["docker", "compose", "--project-directory", str(temporary),
                                "--env-file", str(temporary / ".env"), "config", "--format", "json"],
                               capture=True))
        for service in config["services"].values():
            for port in service.get("ports", []):
                port["host_ip"] = "127.0.0.1"
            if "build" in service:
                service["build"]["context"] = service["build"]["context"].replace(str(temporary), str(release))
            for volume in service.get("volumes", []):
                if volume["type"] == "bind":
                    volume["source"] = volume["source"].replace(str(temporary), str(release))
        # A rendered model is read by Compose again: preserve shell dollars.
        (temporary / "compose.json").write_text(json.dumps(escape_dollars(config)))
        os.chmod(temporary / "compose.json", 0o600)
        atomic_json(temporary / "release.json", {"sha": sha, "slot": slot, "api_port": base + 5,
                                                  "frontend_port": base + 8})
        temporary.rename(release)
    except Exception:
        # Only our exact temporary directory is removed, never a stack or volume.
        shutil.rmtree(temporary)
        raise
    return release


def escape_dollars(value):
    if isinstance(value, str):
        return value.replace("$", "$$")
    if isinstance(value, list):
        return [escape_dollars(item) for item in value]
    if isinstance(value, dict):
        return {key: escape_dollars(item) for key, item in value.items()}
    return value


def smoke(release):
    # The JUP-050 five-step journey, implemented with stdlib on this Linux host.
    from smoke import verify
    verify(release, compose)


def deploy(root, release, run_id=None):
    state_path = root / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    metadata = json.loads((release / "release.json").read_text())
    if state.get("current") == metadata["sha"]:
        print("Already deployed", metadata["sha"])
        return
    previous = state.get("current")
    try:
        compose(release, "build")
        compose(release, "up", "-d", "--no-build", "--wait", "--wait-timeout", "600")
        smoke(release)
    except Exception:
        # The previous slot stays running. Preserve volumes/logs for investigation.
        compose(release, "down", "--remove-orphans")
        atomic_json(root / "failure.json", {"sha": metadata["sha"], "run_id": run_id,
                                            "previous": previous, "time": time.time()})
        raise
    # The pointer changes only after the functional checks pass.
    atomic_json(state_path, {**metadata, "current": metadata["sha"], "previous": previous,
                             "run_id": run_id, "time": time.time()})
    if previous:
        compose(root / "releases" / previous, "down", "--remove-orphans")
    print("Runtime verified", metadata["sha"], "frontend loopback port", metadata["frontend_port"])


def rollback(root):
    state = json.loads((root / "state.json").read_text())
    previous = state.get("previous")
    if not previous:
        raise ValueError("No previous verified release")
    release = root / "releases" / previous
    compose(release, "up", "-d", "--no-build", "--wait", "--wait-timeout", "600")
    smoke(release)
    metadata = json.loads((release / "release.json").read_text())
    atomic_json(root / "state.json", {**metadata, "current": previous,
                                    "previous": state["current"], "time": time.time(), "manual_rollback": True})
    compose(root / "releases" / state["current"], "down", "--remove-orphans")
    print("Rollback verified", previous)


def poll(root):
    head = api("git/ref/heads/develop")["object"]["sha"]
    try:
        runs = api("actions/workflows/cd.yml/runs?branch=develop&per_page=1")["workflow_runs"]
    except urllib.error.HTTPError as error:
        if error.code == 404:
            print("CD workflow not yet integrated; no deployment")
            return
        raise
    eligible = eligible_run(runs, head)
    if not eligible:
        print("No eligible develop revision")
        return
    state_path = root / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    if state.get("current") == head or state.get("manual_rollback"):
        print("Unchanged or manual rollback paused; no deployment")
        return
    cache = root / "repository.git"
    if not cache.exists():
        run(["git", "init", "--bare", str(cache)], capture=True)
    run(["git", "-C", str(cache), "fetch", "--depth=1", REMOTE, "refs/heads/develop"], capture=True)
    fetched = run(["git", "-C", str(cache), "rev-parse", "FETCH_HEAD"], capture=True).strip()
    if fetched != head:
        print("Develop advanced while checking; retry next poll")
        return
    with tempfile.TemporaryDirectory(dir=root) as directory:
        archive = Path(directory) / "source.tar"
        run(["git", "-C", str(cache), "archive", "--output", str(archive), head], capture=True)
        source = Path(directory) / "source"
        with tarfile.open(archive) as tar:
            tar.extractall(source, filter="data")
        slot = 1 - state["slot"] if state else 0
        release = prepare(root, source, head, slot)
    # Do not deploy a superseded revision after a long source preparation.
    if api("git/ref/heads/develop")["object"]["sha"] != head:
        return
    deploy(root, release, eligible["id"])


@contextlib.contextmanager
def lock(root):
    import fcntl  # Host agent runs on Linux; unit tests can import this module on Windows.
    with (root / "deploy.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another deployment is running") from None
        yield


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    initial = commands.add_parser("init")
    initial.add_argument("--port-base", type=int, default=19252)
    commands.add_parser("poll")
    commands.add_parser("rollback")
    commands.add_parser("resume")
    candidate = commands.add_parser("validate-source", help="Isolated operator test; never used by timer")
    candidate.add_argument("--source", type=Path, required=True)
    candidate.add_argument("--sha", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    os.umask(0o077)
    if args.command == "init":
        init(root, args.port_base)
        return
    with lock(root):
        if args.command == "poll":
            poll(root)
        elif args.command == "rollback":
            rollback(root)
        elif args.command == "resume":
            state = json.loads((root / "state.json").read_text())
            state.pop("manual_rollback", None)
            atomic_json(root / "state.json", state)
        else:
            state = json.loads((root / "state.json").read_text()) if (root / "state.json").exists() else {}
            deploy(root, prepare(root, args.source.resolve(), args.sha, 1 - state["slot"] if state else 0))


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        # Never log credentials, response bodies or composed environment values.
        print(f"CD failed: {type(error).__name__}", file=sys.stderr)
        sys.exit(1)
