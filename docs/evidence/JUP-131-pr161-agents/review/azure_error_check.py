"""Source-only check of ApiError traceback compatibility and hash behavior."""

from contextlib import contextmanager
from dataclasses import FrozenInstanceError, asdict
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = "e730dc15fb3feb45a3b346fc9e48332c4608b049"
SOURCE = "apps/azure-cost-api/app/errors.py"
TEST = "apps/azure-cost-api/tests/test_errors.py"


def load_source(name, source):
    module = ModuleType(name)
    sys.modules[name] = module
    exec(compile(source, name, "exec"), module.__dict__)
    return module


@contextmanager
def request_scope():
    yield


old_source = subprocess.check_output(
    ["git", "show", f"{CANDIDATE}:{SOURCE}"], cwd=ROOT, text=True
)
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
assert head == CANDIDATE
before = load_source("review_azure_before", old_source)
after = load_source("review_azure_after", (ROOT / SOURCE).read_text(encoding="utf-8"))
arguments = (429, "TooManyRequests", "Retry later", {"Retry-After": "3"})
old_error = before.ApiError(*arguments)
new_error = after.ApiError(*arguments)
try:
    with request_scope():
        raise old_error
except FrozenInstanceError:
    pass
else:
    raise AssertionError("Original frozen exception must fail traceback restoration")

try:
    with request_scope():
        raise new_error
except after.ApiError as caught:
    assert caught is new_error
else:
    raise AssertionError("Updated exception must propagate unchanged")

saved_traceback = new_error.__traceback__
assert saved_traceback is not None
new_error.__traceback__ = None
assert new_error.__traceback__ is None
new_error.__traceback__ = saved_traceback
assert asdict(old_error) == asdict(new_error)
assert old_error.args == new_error.args
assert before.error_payload(old_error.code, old_error.message) == after.error_payload(
    new_error.code, new_error.message
)
assert callable(before.ApiError.__hash__)
hash(before.ApiError(400, "BadRequest", "Example"))
assert after.ApiError.__hash__ is None
try:
    hash(after.ApiError(400, "BadRequest", "Example"))
except TypeError:
    pass
else:
    raise AssertionError("Mutable dataclass should be unhashable")

result = {
    "reviewer": "/root/pr161_code_review",
    "checked_at": datetime.now().astimezone().isoformat(),
    "python": sys.version.split()[0],
    "head": head,
    "file_sha256": {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in [SOURCE, TEST]},
    "result": "PASS",
    "original_contextmanager_result": "FrozenInstanceError (expected RED)",
    "updated_contextmanager_result": "same ApiError instance propagated (GREEN)",
    "traceback_can_be_cleared_and_restored": True,
    "fields_args_and_payload_unchanged": True,
    "hash_change": "frozen dataclass generated hash -> mutable dataclass unhashable; no dependent repository consumer found by source review",
    "limitations": "Standard-library source execution only, no ASGI, HTTP, cloud, full pytest suite or dependency installation.",
}
destination = ROOT / ".work/pr161-code-review/azure-error-check.json"
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
