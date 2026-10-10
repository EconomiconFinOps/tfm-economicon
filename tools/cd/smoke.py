"""Private development smoke corresponding to JUP-050, without host Node."""
import json
import time
import urllib.request
import uuid


def request(url, data=None, token=None):
    headers = {"Content-Type": "application/json", "X-Tenant-Id": "tenant-core"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = json.dumps(data).encode() if data is not None else None
    with urllib.request.urlopen(urllib.request.Request(url, data=payload, headers=headers), timeout=10) as response:
        body = response.read()
        return json.loads(body) if "json" in response.headers.get("Content-Type", "") else None


def verify(release, compose):
    meta = json.loads((release / "release.json").read_text())
    base = meta["api_port"] - 5
    api = f"http://127.0.0.1:{base + 5}"
    for offset in (5, 6, 7, 8):
        request(f"http://127.0.0.1:{base + offset}" + ("/" if offset == 8 else "/health"))
    print("[OK] 1/5 service health", flush=True)
    # Generated hex secrets are literal, single-quoted dotenv values.
    values = dict(line.split("=", 1) for line in (release / ".env").read_text().splitlines())
    password = values["DEMO_PASSWORD"].strip("'")
    token = request(api + "/auth/login", {"email": "operator@example.com", "password": password})["access_token"]
    if not token:
        raise RuntimeError("Missing authentication token")
    print("[OK] 2/5 demo login", flush=True)
    compose(release, "exec", "-T", "processor", "python", "-m", "app.run_azure_cost_ingestion",
            "--tenant-id", "tenant-core", "--subscription-id", "64e355d7-997c-491d-b0c1-8414dccfcf42", capture=True)
    print("[OK] 3/5 simulator ingestion", flush=True)
    summary = request(api + "/billing/summary?start_date=2024-06-01&end_date=2024-06-21", token=token)
    if summary.get("data_status") == "empty" or not summary.get("totals"):
        raise RuntimeError("Missing billing totals")
    print("[OK] 4/5 billing summary", flush=True)
    job = request(api + "/jobs/ingest", {"tenant_id": "tenant-core", "source": "cd-smoke",
                                        "text_content": "CD DockerServer functional validation."}, token=token)
    job_id = str(uuid.UUID(job["job_id"]))
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        result = compose(release, "exec", "-T", "cockroachdb", "/cockroach/cockroach", "sql",
                         "--insecure", "--format=csv", "--database=defaultdb", "-e",
                         f"SELECT status FROM jobs WHERE id = '{job_id}'", capture=True)
        status = result.strip().splitlines()[-1]
        if status == "completed":
            print("[OK] 5/5 RabbitMQ document job completed", flush=True)
            return
        if status == "failed":
            raise RuntimeError("Document job failed")
        time.sleep(2)
    raise RuntimeError("Document job timed out")
