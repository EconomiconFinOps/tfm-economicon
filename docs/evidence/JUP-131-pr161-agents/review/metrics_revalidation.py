"""Local source-only regression evidence; does not call Terraform, AWS or HTTP."""

from datetime import datetime
from fnmatch import fnmatchcase
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = "e730dc15fb3feb45a3b346fc9e48332c4608b049"
EDGE = "infra/aws-reference/edge.tf"
TEST = "infra/aws-reference/tests/monitoring.tftest.hcl"


def resource(source, kind, name):
    start = source.index(f'resource "{kind}" "{name}" {{')
    stop = source.find('\nresource "', start + 1)
    return source[start:] if stop == -1 else source[start:stop]


def patterns(block):
    match = re.search(r"values\s*=\s*(\[[^\]]*\])", block)
    assert match is not None
    return json.loads(match.group(1))


def priority(block):
    return int(re.search(r"priority\s*=\s*(\d+)", block).group(1))


edge = (ROOT / EDGE).read_text(encoding="utf-8")
monitoring = (ROOT / "infra/aws-reference/monitoring.tf").read_text(encoding="utf-8")
old_edge = subprocess.check_output(
    ["git", "show", f"{CANDIDATE}:{EDGE}"], cwd=ROOT, text=True
)
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
assert head == CANDIDATE
deny = resource(edge, "aws_lb_listener_rule", "deny_metrics")
old_deny = resource(old_edge, "aws_lb_listener_rule", "deny_metrics")
forward = resource(monitoring, "aws_lb_listener_rule", "grafana")
new_patterns = patterns(deny)
old_patterns = patterns(old_deny)
assert new_patterns == ["/metrics", "/metrics/*", "/grafana/metrics*"]
assert len(new_patterns) == 3
assert sum(pattern.count("*") + pattern.count("?") for pattern in new_patterns) == 2
assert all(re.fullmatch(r"[/A-Za-z0-9_*?-]+", pattern) for pattern in new_patterns)
assert priority(deny) == 1 < priority(forward) == 10
assert re.search(r'type\s*=\s*"fixed-response"', deny)
assert re.search(r'status_code\s*=\s*"404"', deny)
assert "http_request_method" not in deny


def denied(url, rules):
    return any(fnmatchcase(urlsplit(url).path, pattern) for pattern in rules)


blocked = [
    "/metrics", "/metrics/", "/metrics/internal",
    "/grafana/metrics", "/grafana/metrics/", "/grafana/metrics/internal",
    "/grafana/metrics?format=prometheus", "/grafana/metrics-prefix",
]
preserved = [
    "/grafana", "/grafana/", "/grafana/login", "/grafana/api/health",
    "/grafana/api/ds/query", "/grafana/api/live/ws",
    "/grafana/public/build/app.js", "/grafana/d/economicon-assistant-evaluation/atlas",
    "/grafana/login?redirect=/grafana/metrics",
]
assert not denied("/grafana/metrics", old_patterns)
assert not denied("/grafana/metrics/internal", old_patterns)
assert all(denied(url, new_patterns) for url in blocked)
assert all(not denied(url, new_patterns) for url in preserved)
result = {
    "reviewer": "/root/pr161_code_review",
    "checked_at": datetime.now().astimezone().isoformat(),
    "head": head,
    "file_sha256": {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in [EDGE, TEST]},
    "result": "PASS",
    "patterns": new_patterns,
    "match_evaluations": len(new_patterns),
    "wildcards": 2,
    "deny_priority": priority(deny),
    "grafana_priority": priority(forward),
    "fixed_status": 404,
    "old_candidate_exposes_grafana_metrics_route": True,
    "blocked_paths": blocked,
    "preserved_paths": preserved,
    "limitations": "Source-only glob evaluation on normal paths; no URI-normalization, Terraform execution, AWS, Docker or HTTP runtime check.",
}
destination = ROOT / ".work/pr161-code-review/metrics-revalidation-check.json"
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
