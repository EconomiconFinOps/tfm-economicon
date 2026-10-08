"""Bounded, read-only diagnostics. Upstream text never crosses this boundary."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import http.client
import json
import threading
import time
from urllib.parse import urlsplit

from sqlalchemy import text

IDS = ("backend", "database", "rabbitmq", "processor", "vector_store", "azure_cost_api", "litellm", "openrouter")
CRITICAL = {"database", "rabbitmq", "vector_store", "processor"}
JOB_STATES = ("publish_pending", "publish_failed", "publish_unknown", "queued", "running", "completed", "failed", "other")
RUN_STATES = ("running", "completed", "failed", "other")
_slots = threading.BoundedSemaphore(4)


def aggregate_status(observations):
    if not observations or all(item["status"] == "unknown" for item in observations):
        return "unknown"
    if any(item["id"] in CRITICAL and item["status"] == "failed" for item in observations):
        return "failed"
    return "ok" if all(item["status"] == "ok" for item in observations) else "degraded"


def observation(status="unknown", reason_code="not_verified", **extra):
    return {"status": status, "reason_code": reason_code, **extra}


def bounded_http_get(url, *, timeout_seconds):
    """Generic service health: preserve the JSON object status contract."""
    return _bounded_http_get(url, timeout_seconds=timeout_seconds, litellm_liveliness=False)


def bounded_litellm_liveliness_get(url, *, timeout_seconds):
    """Pinned LiteLLM liveliness only; this never verifies real inference."""
    return _bounded_http_get(url, timeout_seconds=timeout_seconds, litellm_liveliness=True)


def _bounded_http_get(url, *, timeout_seconds, litellm_liveliness):
    """Finite HTTP primitive, called inside a killable runtime operation for DNS.

    No redirects, credentials, arbitrary client destinations or unbounded reads.
    HTTPConnection's timeout alone is not a DNS deadline; see isolated_operation.
    """
    parsed = urlsplit(url)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        return observation(reason_code="not_configured")
    connection = None
    started = time.monotonic()
    try:
        factory = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        connection = factory(parsed.hostname, port=parsed.port, timeout=timeout_seconds)
        connection.request("GET", parsed.path or "/", headers={"Accept": "application/json"})
        response = connection.getresponse()
        if response.status != 200:
            return observation("failed", "authentication" if response.status in {401, 403} else "upstream_error")
        data = response.read(16_385)
        if len(data) > 16_384:
            return observation(reason_code="invalid_response")
        body = json.loads(data)
        if litellm_liveliness:
            return observation("ok", "none") if isinstance(body, str) and body == "I'm alive!" else observation(reason_code="invalid_response")
        if not isinstance(body, dict) or body.get("status") not in {"ok", "healthy", "degraded"}:
            return observation(reason_code="invalid_response")
        return observation("degraded", "upstream_error") if body["status"] == "degraded" else observation("ok", "none")
    except (TimeoutError, OSError) as exc:
        return observation(reason_code="timeout") if isinstance(exc, TimeoutError) else observation("failed", "connection")
    except (ValueError, http.client.HTTPException):
        return observation(reason_code="invalid_response")
    finally:
        if connection is not None:
            connection.close()
        # The caller supplies timing; bodies, URLs and exceptions are not logged.
        _ = started


def run_probes(probes, *, probe_seconds=2, overall_seconds=5, max_active=4):
    """Fixed finite waves, no pending request queue, shared process-wide slots.

    Runtime callbacks own an isolated-operation deadline including DNS/driver
    cleanup. Other simultaneous aggregations cannot exceed the shared four slots.
    """
    if len(probes) > 32 or not 0 < max_active <= 4:
        raise ValueError("Invalid bounded probe set")
    pending = list(probes.items())
    results = []
    deadline = time.monotonic() + overall_seconds
    while pending:
        admitted = []
        for _ in range(min(max_active, len(pending))):
            identifier, probe = pending.pop(0)
            budget = min(probe_seconds, deadline - time.monotonic())
            if budget <= 0:
                results.append({"id": identifier, **observation(reason_code="timeout")})
            elif not _slots.acquire(blocking=False):
                results.append({"id": identifier, **observation(reason_code="busy")})
            else:
                admitted.append((identifier, probe, budget))
        def execute(identifier, probe, budget):
            started = time.monotonic()
            try:
                result = probe(timeout_seconds=budget)
                if not isinstance(result, dict) or result.get("status") not in {"ok", "degraded", "failed", "unknown"}:
                    result = observation(reason_code="invalid_response")
                return {"id": identifier, "checked_at": datetime.now(timezone.utc),
                        "latency_ms": round((time.monotonic() - started) * 1000, 2), **result}
            except TimeoutError:
                return {"id": identifier, "checked_at": datetime.now(timezone.utc), **observation(reason_code="timeout")}
            except Exception:
                return {"id": identifier, "checked_at": datetime.now(timezone.utc), **observation("failed", "connection")}
            finally:
                _slots.release()
        if admitted:
            with ThreadPoolExecutor(max_workers=len(admitted), thread_name_prefix="health-probe") as executor:
                futures = [executor.submit(execute, *args) for args in admitted]
                results.extend(future.result() for future in futures)
        elif pending:
            # Saturated elsewhere: never wait for a slot or queue more work.
            results.extend({"id": identifier, **observation(reason_code="busy")} for identifier, _ in pending)
            pending.clear()
    return results


def as_utc(value):
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if not isinstance(parsed, datetime):
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def summary(connection, tenant, checked, *, ingestion=False):
    table = "azure_cost_ingestion_runs" if ingestion else "jobs"
    states = RUN_STATES if ingestion else JOB_STATES
    latest_name = "last_completed_at" if ingestion else "last_updated_at"
    unavailable = {"data_status": "unavailable", "counts": None, "failed_last_24h": None, latest_name: None}
    try:
        counts = dict.fromkeys(states, 0)
        # Table/column names are constants; the authorized scope is a parameter.
        for state, count in connection.execute(text(f"SELECT status, COUNT(*) FROM {table} WHERE tenant_id=:tenant GROUP BY status"), {"tenant": tenant}):
            counts[state if state in states else "other"] += int(count)
        terminal = "COALESCE(completed_at, started_at)" if ingestion else "updated_at"
        failed_predicate = "status='failed'" if ingestion else "status IN ('failed','publish_failed')"
        failed = connection.execute(text(f"SELECT COUNT(*) FROM {table} WHERE tenant_id=:tenant AND {failed_predicate} AND {terminal} >= :start AND {terminal} <= :end"), {"tenant": tenant, "start": checked - timedelta(hours=24), "end": checked}).scalar_one()
        column = "completed_at" if ingestion else "updated_at"
        predicate = " AND status='completed'" if ingestion else ""
        latest = connection.execute(text(f"SELECT MAX({column}) FROM {table} WHERE tenant_id=:tenant{predicate}"), {"tenant": tenant}).scalar_one()
        return {"data_status": "available" if sum(counts.values()) else "empty", "counts": counts,
                "failed_last_24h": int(failed), latest_name: as_utc(latest)}
    except Exception:
        return unavailable


def unavailable_summary(*, ingestion=False):
    return {"data_status": "unavailable", "counts": None, "failed_last_24h": None,
            "last_completed_at" if ingestion else "last_updated_at": None}
