"""JUP-052. Private, disposable development CD; no third-party dependencies."""
import argparse
import contextlib
import hashlib
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
            and (latest.get("head_repository") or {}).get("full_name") == REPOSITORY):
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
                  DATABASE_URL="cockroachdb+psycopg://root@cockroachdb:26257/defaultdb?sslmode=disable",
                  VECTOR_DATABASE_URL=f"postgresql+psycopg://postgres:{values['POSTGRES_PASSWORD']}@postgres-pgvector:5432/embeddings",
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
    # All operator/timer callers hold the root lock. An interrupted copy has
    # never been started, and may safely be discarded before retrying this SHA.
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True, mode=0o700)
    try:
        shutil.copytree(source, temporary, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".git", "node_modules", ".venv", ".env*", "__pycache__"))
        # data-filtered Git archives extracted under our private umask have
        # 0700 directories. Docker COPY preserves those modes, preventing the
        # non-root app user from traversing its code inside the image.
        # Only copied source directories become traversable; the enclosing
        # release/root and generated credentials remain private on the host.
        for directory, children, _ in os.walk(temporary):
            for child in children:
                path = Path(directory) / child
                if not path.is_symlink():
                    os.chmod(path, 0o755)
        os.chmod(temporary, 0o700)
        base = json.loads((root / "config.json").read_text())["port_base"] + slot * 100
        values = json.loads((root / "secrets.json").read_text())
        values.update({name: str(base + offset) for name, offset in PORTS.items()})
        namespace = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:12]
        values.update(COMPOSE_PROJECT_NAME=f"economicon-cd-{namespace}-{sha[:12]}",
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
        # Compose's JSON renderer already preserves escaped shell dollars ($$).
        (temporary / "compose.json").write_text(json.dumps(config))
        os.chmod(temporary / "compose.json", 0o600)
        atomic_json(temporary / "release.json", {"sha": sha, "slot": slot, "api_port": base + 5,
                                                  "frontend_port": base + 8})
        temporary.rename(release)
    except Exception:
        # Only our exact temporary directory is removed, never a stack or volume.
        shutil.rmtree(temporary)
        raise
    return release


def smoke(release):
    # The JUP-050 five-step journey, implemented with stdlib on this Linux host.
    from smoke import verify
    verify(release, compose)


class CleanupError(RuntimeError):
    def __init__(self, failures):
        self.failures = failures
        super().__init__(f"Cleanup failed for {len(failures)} releases/copies")


def reconcile(root, current):
    """Stop only this root's inactive releases; keep sources and named volumes.

    Includes previous: it must be stopped to free the opposite slot, but remains
    available for rollback. Scanning is durable even after death immediately
    after state promotion; a failed down is retried on the next locked poll.
    """
    failures = []
    for release in sorted((root / "releases").glob("*")):
        try:
            if SHA.fullmatch(release.name) and release.name != current:
                compose(release, "down", "--remove-orphans")
            elif release.name.endswith(".preparing") and SHA.fullmatch(release.name[:-10]):
                shutil.rmtree(release)
        except Exception as error:
            failures.append({"release": release.name, "error_type": type(error).__name__})
    if failures:
        raise CleanupError(failures)


def event(root, value):
    directory = root / "events"
    directory.mkdir(mode=0o700, exist_ok=True)
    atomic_json(directory / f"{time.time_ns()}-{secrets.token_hex(4)}.json", value)


def evidence(action, *args, **kwargs):
    """Observability is best effort; never replace a runtime/cleanup cause."""
    try:
        action(*args, **kwargs)
    except Exception as error:
        print(f"Evidence unavailable: {type(error).__name__}; inspect runtime state", file=sys.stderr)


def recovery_status(root, errors):
    path = root / "recovery.json"
    if errors:
        evidence(atomic_json, path, {**errors[-1], "errors": errors, "time": time.time()})
    else:
        evidence(path.unlink, missing_ok=True)


def record_failure(root, release, previous, run_id, error, permanent=True, reason="candidate-failed"):
    # Store types, never exception messages, environment or subprocess output.
    failure = {"sha": release.name, "run_id": run_id, "previous": previous,
               "time": time.time(), "error_type": type(error).__name__, "reason": reason}
    if permanent:
        evidence(atomic_json, root / "failure.json", failure)
    # Every attempt is historical; temporary eligibility failures/cancelled
    # promotions never overwrite the permanent candidate quarantine marker.
    evidence(event, root, failure)
    try:
        compose(release, "down", "--remove-orphans")
    except Exception as cleanup_error:
        failure["cleanup_error_type"] = type(cleanup_error).__name__
        if permanent:
            evidence(atomic_json, root / "failure.json", failure)
        evidence(event, root, failure)
        print("Candidate cleanup failed; reconciliation will retry", file=sys.stderr)


def resolve_failure(root, current):
    def update():
        path = root / "failure.json"
        if path.exists():
            failure = json.loads(path.read_text())
            if failure.get("sha") == current and not failure.get("resolved_at"):
                atomic_json(path, {**failure, "resolved_at": time.time()})
    evidence(update)


def transition_cleanup(root, current):
    # State already committed: record cleanup separately, never undo promotion.
    try:
        reconcile(root, current)
    except CleanupError as error:
        detail = {"phase": "cleanup", "error_type": type(error).__name__, "releases": error.failures}
        recovery_status(root, [detail])
        evidence(event, root, {**detail, "sha": current, "reason": "cleanup-pending", "time": time.time()})
        print("State already changed: current", current, "; cleanup pending; next poll retries", file=sys.stderr)
        raise
    recovery_status(root, [])


def deploy(root, release, run_id=None, expected_head=None):
    state_path = root / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    metadata = json.loads((release / "release.json").read_text())
    if state.get("current") == metadata["sha"]:
        resolve_failure(root, metadata["sha"])
        print("Already deployed", metadata["sha"])
        return
    previous = state.get("current")
    try:
        compose(release, "build")
        compose(release, "up", "-d", "--no-build", "--wait", "--wait-timeout", "600")
        smoke(release)
    except Exception as error:
        # Preserve the original cause even when down fails. Volumes remain;
        # container logs do not survive a successful down (use journal).
        record_failure(root, release, previous, run_id, error)
        raise
    if expected_head:
        try:
            head = api("git/ref/heads/develop")["object"]["sha"]
        except Exception as error:
            record_failure(root, release, previous, run_id, error, permanent=False,
                           reason="eligibility-unavailable")
            raise
        if head != expected_head:
            record_failure(root, release, previous, run_id, RuntimeError(), permanent=False,
                           reason="superseded")
            print("Develop advanced before promotion; retry next eligible SHA")
            return
    # The pointer changes only after the functional checks pass.
    atomic_json(state_path, {**metadata, "current": metadata["sha"], "previous": previous,
                             "run_id": run_id, "time": time.time()})
    resolve_failure(root, metadata["sha"])
    transition_cleanup(root, metadata["sha"])
    print("Runtime verified", metadata["sha"], "frontend loopback port", metadata["frontend_port"])


def rollback(root):
    state = json.loads((root / "state.json").read_text())
    repeated = state.get("manual_rollback", False)
    previous = state["current"] if repeated else state.get("previous")
    if not previous:
        raise ValueError("No previous verified release")
    release = root / "releases" / previous
    try:
        compose(release, "up", "-d", "--no-build", "--wait", "--wait-timeout", "600")
        smoke(release)
    except Exception as error:
        if repeated:
            recovery_status(root, [{"phase": "current", "error_type": type(error).__name__}])
        else:
            record_failure(root, release, state["current"], None, error)
        raise
    metadata = json.loads((release / "release.json").read_text())
    if not repeated:
        atomic_json(root / "state.json", {**metadata, "current": previous,
                                        "previous": state["current"], "time": time.time(), "manual_rollback": True})
    else:
        print("Rollback already applied; verifying current and retrying cleanup", previous)
    resolve_failure(root, previous)
    transition_cleanup(root, previous)
    print("Rollback verified", previous)


def poll(root):
    state_path = root / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    recovery_errors = []
    # Continue querying eligibility if recovery/cleanup fails; require cleanup
    # to succeed before reusing the inactive slot for an eligible candidate.
    try:
        reconcile(root, state.get("current"))
    except Exception as error:
        recovery_errors.append({"phase": "cleanup", "error_type": type(error).__name__,
                                "releases": getattr(error, "failures", [])})
        print("Inactive cleanup failed; eligibility will still be checked", file=sys.stderr)
    if state.get("current"):
        # Recover after host reboot even when GitHub is offline; no build or new SHA.
        try:
            compose(root / "releases" / state["current"], "up", "-d", "--no-build", "--wait", "--wait-timeout", "600")
            resolve_failure(root, state["current"])
        except Exception as error:
            recovery_errors.append({"phase": "current", "error_type": type(error).__name__})
            print("Current recovery failed; eligibility will still be checked", file=sys.stderr)
    recovery_status(root, recovery_errors)
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
    if state.get("current") == head or state.get("manual_rollback"):
        print("Unchanged or manual rollback paused; no deployment")
        return
    failure_path = root / "failure.json"
    failure = json.loads(failure_path.read_text()) if failure_path.exists() else {}
    if failure.get("sha") == head and not failure.get("retry_allowed"):
        print("Failed revision paused; use resume to retry")
        return
    try:
        reconcile(root, state.get("current"))
    except Exception as error:
        recovery_errors = [e for e in recovery_errors if e["phase"] != "cleanup"]
        recovery_errors.append({"phase": "cleanup", "error_type": type(error).__name__,
                                "releases": getattr(error, "failures", [])})
        recovery_status(root, recovery_errors)
        raise
    recovery_errors = [e for e in recovery_errors if e["phase"] != "cleanup"]
    recovery_status(root, recovery_errors)
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
    deploy(root, release, eligible["id"], expected_head=head)


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
            state_path = root / "state.json"
            state = json.loads(state_path.read_text()) if state_path.exists() else {}
            state.pop("manual_rollback", None)
            if state:
                atomic_json(state_path, state)
            failure_path = root / "failure.json"
            if failure_path.exists():
                failure = json.loads(failure_path.read_text())
                atomic_json(failure_path, {**failure, "retry_allowed": True})
        else:
            state = json.loads((root / "state.json").read_text()) if (root / "state.json").exists() else {}
            if state.get("manual_rollback"):
                raise ValueError("Manual rollback paused; resume before operator validation")
            if not SHA.fullmatch(args.sha) or (root / "releases" / args.sha).exists():
                raise ValueError("Validation requires a new full SHA label; existing releases are immutable")
            reconcile(root, state.get("current"))
            deploy(root, prepare(root, args.source.resolve(), args.sha, 1 - state["slot"] if state else 0))


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        # Never log credentials, response bodies or composed environment values.
        print(f"CD failed: {type(error).__name__}", file=sys.stderr)
        sys.exit(1)
