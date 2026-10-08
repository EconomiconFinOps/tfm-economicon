"""Runtime adapters with disposable connections and killable DNS/driver work."""
from datetime import datetime, timedelta, timezone
import hashlib
import http.client
import json
import logging
import math
import multiprocessing
import os
import re
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit
from uuid import uuid4

import pika
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.services.health_provider_check import GUARANTEES, HealthProviderCheck, ProviderDiagnosticFailure, amount
from app.services.system_health import bounded_http_get, bounded_litellm_liveliness_get, observation, summary, unavailable_summary

INSTANCE_ID = uuid4().hex
_provider_lock = threading.Lock()
_provider = None
_nonce_reported = False


def _db_read(connection, tenant, checked):
    connection.execute(text("SELECT 1"))
    return {"jobs": summary(connection, tenant, checked), "ingestion": summary(connection, tenant, checked, ingestion=True)}


def _database(url, tenant, checked, timeout):
    engine = create_engine(url, connect_args={"connect_timeout": max(1, math.ceil(timeout))}, pool_size=1, max_overflow=0)
    result = observation("ok", "none")
    try:
        # Separate read-only transactions: a missing table does not poison the
        # other summary, or turn a reachable database into a connector failure.
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text(f"SET LOCAL statement_timeout = '{max(1, int(timeout * 1000))}ms'"))
            connection.execute(text("SELECT 1"))
        for name, ingestion in (("jobs", False), ("ingestion", True)):
            try:
                with engine.connect() as connection:
                    connection.execute(text("SET TRANSACTION READ ONLY"))
                    connection.execute(text(f"SET LOCAL statement_timeout = '{max(1, int(timeout * 1000))}ms'"))
                    result[name] = summary(connection, tenant, checked, ingestion=ingestion)
            except Exception:
                result[name] = unavailable_summary(ingestion=ingestion)
        return result
    finally:
        engine.dispose()


def _vector(url, timeout):
    engine = create_engine(url, connect_args={"connect_timeout": max(1, math.ceil(timeout))}, pool_size=1, max_overflow=0)
    try:
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text(f"SET LOCAL statement_timeout = '{max(1, int(timeout * 1000))}ms'"))
            connection.execute(text("SELECT 1"))
            extension = connection.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")).scalar_one()
            tables = all(connection.execute(text("SELECT to_regclass(:name) IS NOT NULL"), {"name": name}).scalar_one() for name in ("knowledge_documents", "document_chunks", "chunk_embeddings"))
            if not extension or not tables:
                return observation("failed", "not_initialized")
            return observation("ok", "none")
    finally:
        engine.dispose()


def _queue(url, timeout):
    parameters = pika.URLParameters(url)
    parameters.socket_timeout = max(0.1, timeout * 0.7)
    parameters.stack_timeout = max(0.2, timeout * 0.9)
    parameters.blocked_connection_timeout = max(0.1, timeout * 0.7)
    parameters.connection_attempts = 1
    connection = None
    try:
        connection = pika.BlockingConnection(parameters)
        return observation("ok", "none") if connection.is_open else observation("failed", "connection")
    finally:
        if connection is not None and connection.is_open:
            connection.close()


def _provider_request(base_url, key, payload, timeout, certified_route, check_id):
    parsed = urlsplit(base_url)
    factory = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    connection = factory(parsed.hostname, port=parsed.port, timeout=timeout)
    try:
        path = parsed.path.rstrip("/") + "/chat/completions"
        # Internal policy prices are Decimal-safe strings. The wire contract
        # uses JSON numbers; retain their exact decimal lexemes without float
        # rounding or a permissive custom encoder.
        prices = payload["provider"]["max_price"]
        numeric_prices = "{\"prompt\":" + str(amount(prices["prompt"])) + ",\"completion\":" + str(amount(prices["completion"])) + "}"
        body = json.dumps(payload).replace(json.dumps(prices), numeric_prices, 1)
        connection.request("POST", path, body=body, headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "X-Request-ID": check_id})
        response = connection.getresponse()
        if response.status != 200:
            raise ProviderDiagnosticFailure("authentication" if response.status in {401, 403} else "upstream_error")
        raw = response.read(16_385)
        if len(raw) > 16_384:
            raise ValueError("Unverified provider result")
        body = json.loads(raw)
        choices = body.get("choices", [])
        valid = (isinstance(choices, list) and len(choices) == 1
                 and choices[0].get("finish_reason") == "stop"
                 and choices[0].get("message", {}).get("content", "").strip().upper() == "OK"
                 and isinstance(body.get("id"), str) and 0 < len(body["id"]) <= 256)
        model = body.get("model")
        # Routing is certified out of band for the dedicated gateway/alias.
        # A body model name alone is never sufficient to certify the route.
        return {"model": model, "provider": certified_route, "route_verified": certified_route == "deepinfra/fp4",
                "result_valid": valid, "usage": body.get("usage", {}),
                "cost_usd": response.getheader("x-litellm-response-cost"), "check_id": check_id}
    finally:
        connection.close()


def _child(pipe, operation, args, timeout):
    # Driver/library exception text can contain credentials or upstream bodies.
    # This isolated diagnostic never emits their stdout/stderr/logging.
    logging.disable(logging.CRITICAL)
    with open(os.devnull, "w") as sink:
        os.dup2(sink.fileno(), 1)
        os.dup2(sink.fileno(), 2)
        try:
            if operation == "database":
                result = _database(*args, timeout)
            elif operation == "vector":
                result = _vector(*args, timeout)
            elif operation == "queue":
                result = _queue(*args, timeout)
            elif operation == "http":
                result = bounded_http_get(*args, timeout_seconds=timeout)
            elif operation == "litellm_liveliness":
                result = bounded_litellm_liveliness_get(*args, timeout_seconds=timeout)
            elif operation == "provider":
                result = _provider_request(*args[:3], timeout, args[3], args[4])
            elif operation == "port":
                result = observation("ok", "none") if args[0].ping() else observation("failed", "connection")
            else:
                raise ValueError("Unknown diagnostic operation")
            pipe.send((True, result))
        except ProviderDiagnosticFailure as failure:
            pipe.send((False, failure.reason))
        except TimeoutError:
            pipe.send((False, "timeout"))
        except OSError:
            pipe.send((False, "connection"))
        except Exception:
            pipe.send((False, "connection" if operation != "provider" else "invalid_response"))
        finally:
            pipe.close()


def isolated_operation(operation, args, *, timeout_seconds):
    """Hard total deadline includes spawn, DNS, connect, query/read and teardown.

    No pooled business connection is reused. Termination closes child sockets
    and prevents orphaned work; supervisor slots are released only after join.
    """
    context = multiprocessing.get_context("fork" if operation == "port" and "fork" in multiprocessing.get_all_start_methods() else "spawn")
    receive, send = context.Pipe(duplex=False)
    process = context.Process(target=_child, args=(send, operation, args, max(0.01, timeout_seconds - 0.15)), daemon=True)
    deadline = time.monotonic() + timeout_seconds
    try:
        process.start()
        send.close()
        remaining = max(0, deadline - time.monotonic() - 0.1)
        if not receive.poll(remaining):
            raise TimeoutError()
        success, result = receive.recv()
        if not success:
            if result == "timeout":
                raise TimeoutError()
            if operation == "provider" and result in {"authentication", "connection", "upstream_error"}:
                raise ProviderDiagnosticFailure(result)
            raise ValueError("Unverified diagnostic")
        return result
    finally:
        receive.close()
        send.close()
        if process.pid is not None:
            if process.is_alive():
                process.terminate()
            process.join(timeout=max(0.01, deadline - time.monotonic()))
            if process.is_alive():
                process.kill()
                process.join()
            process.close()


def database_probe(database, tenant, checked, *, timeout_seconds):
    engine = getattr(database, "engine", None)
    if isinstance(engine, Engine) and engine.dialect.name == "sqlite":
        # SQLite is local and has no network/DNS. Real scoped SQL fixtures use
        # the same bounded reader, with a progress deadline and no mutations.
        deadline = time.monotonic() + timeout_seconds
        with engine.connect() as connection:
            driver = connection.connection.driver_connection
            driver.set_progress_handler(lambda: int(time.monotonic() >= deadline), 100)
            try:
                return {**observation("ok", "none"), **_db_read(connection, tenant, checked)}
            finally:
                driver.set_progress_handler(None, 0)
    if isinstance(engine, Engine):
        return isolated_operation("database", (engine.url.render_as_string(hide_password=False), tenant, checked), timeout_seconds=timeout_seconds)
    return isolated_operation("port", (database,), timeout_seconds=timeout_seconds)


def vector_probe(vector_store, *, timeout_seconds):
    engine = getattr(vector_store, "engine", None)
    if isinstance(engine, Engine):
        return isolated_operation("vector", (engine.url.render_as_string(hide_password=False),), timeout_seconds=timeout_seconds)
    return {**isolated_operation("port", (vector_store,), timeout_seconds=timeout_seconds), "source_kind": "mock"}


def queue_probe(queue, settings, *, timeout_seconds):
    # Native broker adapter owns a fresh connection; generic injected ports are
    # contained too, but their result is explicitly mock provenance.
    from app.services.rabbitmq_queue import RabbitMQQueue
    if isinstance(RabbitMQQueue, type) and isinstance(queue, RabbitMQQueue):
        return isolated_operation("queue", (settings.rabbitmq_url.get_secret_value(),), timeout_seconds=timeout_seconds)
    return {**isolated_operation("port", (queue,), timeout_seconds=timeout_seconds), "source_kind": "mock"}


def http_probe(url, *, timeout_seconds):
    if not url:
        return observation(reason_code="not_configured")
    return isolated_operation("http", (url,), timeout_seconds=timeout_seconds)


def litellm_liveliness_probe(url, *, timeout_seconds):
    if not url:
        return observation(reason_code="not_configured")
    return isolated_operation("litellm_liveliness", (url,), timeout_seconds=timeout_seconds)


def _policy_utc(value):
    if not isinstance(value, str):
        raise ValueError("Uncertified date")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("Uncertified date")
    return parsed


def _read_policy(settings):
    if not settings.health_provider_enabled or not settings.health_provider_policy_path or not settings.health_provider_api_key:
        raise ValueError("Provider admission unavailable")
    # Read a bounded, operator-owned, read-only mounted certificate. No live
    # admin key, upstream key, pricing lookup or ledger mutation in the backend.
    with Path(settings.health_provider_policy_path).open("rb") as stream:
        raw = stream.read(16_385)
    if len(raw) > 16_384:
        raise ValueError("Provider admission unavailable")
    policy = json.loads(raw)
    now = datetime.now(timezone.utc)
    price_checked = _policy_utc(policy["price_checked_at"])
    valid_from = _policy_utc(policy["valid_from"])
    valid_until = _policy_utc(policy["valid_until"])
    digest_pattern = r"[0-9a-f]{64}"
    key_digest = hashlib.sha256(settings.health_provider_api_key.get_secret_value().encode("utf-8")).hexdigest()
    if (not price_checked <= valid_from <= now < valid_until <= price_checked + timedelta(hours=24)
            or policy.get("instance_id") != INSTANCE_ID
            or policy.get("single_replica_verified") is not True
            or policy.get("single_process_verified") is not True
            or policy.get("credential_dedicated") is not True
            or policy.get("credential_alias_only") is not True
            or policy.get("credential_sha256") != key_digest
            or policy.get("gateway_base_url") != settings.litellm_base_url
            or not re.fullmatch(digest_pattern, str(policy.get("routing_config_sha256", "")))
            or policy.get("routing_alias") != "economicon-chat"
            or policy.get("routing_model") != "openrouter/z-ai/glm-5.2"
            or policy.get("routing_provider") != "deepinfra/fp4"
            or policy.get("input_envelope_certified") is not True
            or policy.get("gateway_retries") != 0 or type(policy.get("gateway_retries")) is not int
            or policy.get("router_retries") != 0 or type(policy.get("router_retries")) is not int
            or policy.get("reasoning_enabled") is not False
            or policy.get("allow_fallbacks") is not False or policy.get("privacy_verified") is not True
            or not all(policy.get(name) is True for name in GUARANTEES)
            or not all(isinstance(policy.get(name), str) and 0 < len(policy[name]) <= 256
                       for name in ("credential_id", "execution_id", "ledger_reference", "authorization_reference"))
            or type(policy.get("execution_calls_limit")) is not int or not 0 < policy["execution_calls_limit"] <= 24
            or type(policy.get("known_execution_calls")) is not int
            or not 0 <= policy["known_execution_calls"] <= policy["execution_calls_limit"]
            or not isinstance(policy.get("additional_limits_usd"), list) or not policy["additional_limits_usd"]):
        raise ValueError("Provider admission unavailable")
    # Carry recorded spend and historical uncertainty forward truthfully.
    # Nonzero uncertainty consumes capacity rather than the call allowance.
    amount(policy["known_spend_usd"])
    amount(policy["uncertain_usd"])
    if amount(policy["pending_usd"]) != 0:
        raise ValueError("Pending diagnostic operation")
    service = HealthProviderCheck(policy=policy, transport=None)
    service._reserve_bound()
    return policy, hashlib.sha256(raw).hexdigest()


class RuntimeTransport:
    def __init__(self, settings, digest):
        self.settings, self.digest = settings, digest
    def preflight(self):
        policy, digest = _read_policy(self.settings)
        if digest != self.digest:
            raise ValueError("Admission certificate changed")
        return policy

    def __call__(self, payload, *, timeout_seconds):
        # Verify again after reservation, immediately before possible network I/O.
        policy = self.preflight()
        return isolated_operation("provider", (self.settings.litellm_base_url,
                                  self.settings.health_provider_api_key.get_secret_value(), payload,
                                  policy["routing_provider"], uuid4().hex), timeout_seconds=timeout_seconds)


def provider_service(settings):
    global _provider, _nonce_reported
    with _provider_lock:
        if _provider is not None:
            return _provider
        try:
            policy, digest = _read_policy(settings)
        except Exception:
            # Non-secret nonce binds truthful ordinary state to this process.
            if settings.health_provider_enabled and not _nonce_reported:
                logging.getLogger(__name__).info("health_provider_admission_unavailable instance_id=%s", INSTANCE_ID)
                _nonce_reported = True
            return HealthProviderCheck(policy={}, transport=None)
        _provider = HealthProviderCheck(policy=policy, transport=RuntimeTransport(settings, digest))
        return _provider
