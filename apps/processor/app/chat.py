"""Private authenticated chat ASGI surface, separate from public health.

SQL ownership/current-claim checks precede any gateway dispatch. Only the signed
backend may submit claims; nonce and attempt replay cannot create a second call.
"""

import asyncio
import hashlib
import hmac
import json
import time
import os
from contextlib import aclosing, asynccontextmanager
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from sqlalchemy import text
from app.core.runtime_secrets import StartupError


def configured_capacity():
    value = os.getenv("CHAT_MAX_ACTIVE", "8").strip()
    if value not in {"5", "6", "7", "8"}:
        raise StartupError("Chat capacity configuration is invalid.")
    return int(value)


def validate_capacity(value):
    if type(value) is not int or not 5 <= value <= 8:
        raise StartupError("Chat capacity configuration is invalid.")
    return value


def encode(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def epoch(value):
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


@asynccontextmanager
async def resource_lifespan(app):
    app.state.chat_resources = None
    app.state.chat_prompt_version = None
    app.state.summary_resources = None
    app.state.summary_version = None
    if os.getenv("CHAT_ENABLED", "false").lower() == "true":
        app.state.chat_capacity = (
            validate_capacity(app.state.chat_capacity)
            if hasattr(app.state, "chat_capacity")
            else configured_capacity()
        )
        try:
            from app.core.chat_resources import load_resources

            resources = await asyncio.to_thread(
                load_resources,
                os.getenv("CHAT_RESOURCE_DIRECTORY"),
                os.getenv("CHAT_TOKENIZER_FILE"),
            )
            app.state.chat_resources = resources
            app.state.chat_prompt_version = resources.prompt_version
        except Exception:
            app.state.chat_resources = None
        if app.state.chat_resources is not None:
            try:
                from app.core.summary_resources import (
                    load_resources as load_summary_resources,
                )

                summary = await asyncio.to_thread(
                    load_summary_resources,
                    os.getenv("SUMMARY_RESOURCE_DIRECTORY"),
                    os.getenv("CHAT_TOKENIZER_FILE"),
                )
                app.state.summary_resources = summary
                app.state.summary_version = summary.summary_version
            except Exception:
                # A missing/changed optional memory never disables main chat.
                app.state.summary_resources = None
    from app.clients.summary_gateway import (
        configured_gateway as configured_summary_gateway,
    )

    app.state.summary_gateway = (
        configured_summary_gateway()
        if app.state.summary_resources is not None
        and os.getenv("SUMMARY_ENABLED", "false") == "true"
        else None
    )
    app.state.summary_jobs = {}
    try:
        yield
    finally:
        from app.summary import shutdown as shutdown_summary

        await shutdown_summary(app)
        app.state.chat_resources = None
        app.state.chat_prompt_version = None
        app.state.summary_resources = None
        app.state.summary_version = None


def create_chat_app():
    app = FastAPI(
        title="Private Chat",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=resource_lifespan,
    )
    app.state.chat_boot_id = str(uuid4())
    app.state.chat_nonces = {}
    app.state.chat_attempts = {}
    app.state.chat_gate = Lock()

    @app.middleware("http")
    async def authenticated(request, call_next):
        key = getattr(app.state, "chat_signing_key", None)
        if not isinstance(key, bytes) or len(key) < 32:
            return JSONResponse({"code": "chat_not_ready"}, 503)
        headers = request.headers
        try:
            at = headers["X-Chat-Time"]
            nonce = headers["X-Chat-Nonce"]
            if (
                headers.get("X-Chat-Key-Id") != "chat-v2"
                or abs(time.time() - int(at)) > 30
                or str(UUID(nonce)) != nonce
                or request.url.query
            ):
                raise ValueError()
            chunks = []
            size = 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 2 * 1024 * 1024:
                    return JSONResponse({"code": "input_limit"}, 413)
                chunks.append(chunk)
            raw = b"".join(chunks)
            message = f"chat-v2\n{request.method}\n{request.url.path}\n{at}\n{nonce}\n{hashlib.sha256(raw).hexdigest()}".encode()
            if not hmac.compare_digest(
                headers.get("X-Chat-Signature", ""),
                hmac.new(key, message, hashlib.sha256).hexdigest(),
            ):
                raise ValueError()
            now = time.time()
            with app.state.chat_gate:
                nonces = app.state.chat_nonces
                for old in [old for old, expiry in nonces.items() if expiry <= now]:
                    del nonces[old]
                if nonce in nonces:
                    raise ValueError()
                if len(nonces) >= 4096:
                    return JSONResponse({"code": "nonce_capacity"}, 503)
                nonces[nonce] = now + 180
            request.state.chat_body = raw
            request.state.chat_nonce = nonce
        except (KeyError, ValueError, TypeError):
            return JSONResponse({"code": "unauthorized"}, 401)
        return await call_next(request)

    def signed_response(request, value, status=200):
        raw = encode(value)
        nonce = request.state.chat_nonce
        signature = hmac.new(
            app.state.chat_signing_key,
            f"chat-v2-response\n{nonce}\n{status}\n{hashlib.sha256(raw).hexdigest()}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return Response(
            raw,
            status,
            media_type="application/json",
            headers={
                "X-Chat-Nonce": nonce,
                "X-Chat-Signature": signature,
                "Cache-Control": "no-store",
            },
        )

    @app.get("/internal/chat/v2/descriptor")
    async def descriptor(request: Request):
        version = getattr(app.state, "chat_prompt_version", None)
        if not version:
            return signed_response(request, {"code": "chat_not_ready"}, 503)
        try:
            capacity = validate_capacity(getattr(app.state, "chat_capacity", 8))
        except StartupError:
            return signed_response(request, {"code": "capacity_invalid"}, 503)
        value = {
            "v": 2,
            "boot_id": app.state.chat_boot_id,
            "prompt_version": version,
            "capacity": capacity,
        }
        from app.core.config import get_settings

        value["tool_protocol"] = (
            "mock-direct-v1"
            if get_settings().llm_provider == "mock"
            else "server-documentation-v4"
        )
        resources = getattr(app.state, "chat_resources", None)
        if resources is not None:
            value.update(
                tokenizer_sha256=resources.tokenizer_sha256,
                response_schema_sha256=resources.response_schema_sha256,
                context_budget=resources.context_budget,
            )
        return signed_response(request, value)

    @app.get("/internal/chat/v2/summary/descriptor")
    async def summary_descriptor(request: Request):
        resources = getattr(app.state, "summary_resources", None)
        if resources is None:
            return signed_response(request, {"code": "summary_not_ready"}, 503)
        value = {
            "v": 2,
            "boot_id": app.state.chat_boot_id,
            "summary_version": resources.summary_version,
            "manifest_sha256": hashlib.sha256(resources.manifest_bytes).hexdigest(),
            "tokenizer_sha256": resources.tokenizer_sha256,
            "response_schema_sha256": resources.response_schema_sha256,
            "context_budget": resources.context_budget,
        }
        from app.core.chat_admission import POLICY

        try:
            capacity = validate_capacity(getattr(app.state, "chat_capacity", 8))
        except StartupError:
            return signed_response(request, {"code": "capacity_invalid"}, 503)
        value.update(
            capacity=capacity,
            admission_policy=POLICY,
            summary_ready=getattr(app.state, "summary_gateway", None) is not None,
        )
        return signed_response(request, value)

    def owned(claim, cancel=False):
        database = getattr(app.state, "chat_database", None)
        if database is None:
            return None
        with database.engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT o.* FROM chat_operations o JOIN conversations c ON "
                        "c.id=o.conversation_id AND c.tenant_id=o.tenant_id AND c.user_id=o.user_id "
                        "WHERE o.operation_id=:operation_id AND o.tenant_id=:tenant_id AND o.user_id=:user_id "
                        "AND o.conversation_id=:conversation_id AND o.current_attempt_id=:attempt_id"
                    ),
                    claim,
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        row = dict(row)
        control = row["private_control"]
        if isinstance(control, str):
            control = json.loads(control)
        if cancel:
            if (
                row["state"] != "cancelled"
                or claim.get("number") != row["attempt_count"]
                or claim.get("boot_id") != app.state.chat_boot_id
                or control.get("boot_id") != claim.get("boot_id")
                or not isinstance(claim.get("capability"), str)
                or not hmac.compare_digest(
                    control.get("capability", ""), claim["capability"]
                )
                or claim.get("input_hash") != row["input_hash"]
            ):
                return None
            return row
        deadline = claim.get("deadline")
        if (
            row["state"] != "active"
            or type(claim.get("number")) is not int
            or claim["number"] != row["attempt_count"]
            or type(deadline) not in (int, float)
            or not time.time() < deadline <= epoch(row["attempt_deadline"])
        ):
            return None
        if (
            claim.get("boot_id") != app.state.chat_boot_id
            or control.get("boot_id") != claim["boot_id"]
            or not isinstance(claim.get("capability"), str)
            or not hmac.compare_digest(
                control.get("capability", ""), claim["capability"]
            )
            or claim.get("input_hash") != row["input_hash"]
        ):
            return None
        context = claim.get("context")
        if not isinstance(context, dict) or context.get("prompt_version") != getattr(
            app.state, "chat_prompt_version", None
        ):
            return None
        frozen = row.get("canonical_input")
        if isinstance(frozen, str):
            frozen = json.loads(frozen)
        if frozen is not None and encode(frozen["context"]) != encode(context):
            return None
        correction = control.get("correction")
        if correction:
            from app.core.chat_correction import INSTRUCTIONS, verify_cache
            expected = {**correction, "cache": control.get("recovery")}
            if (claim.get("correction") != expected or not correction.get("claimed")
                or correction.get("attempt_id") != claim.get("attempt_id")
                or correction.get("number") != claim.get("number")
                or correction.get("deadline") != deadline
                or correction.get("code") not in INSTRUCTIONS):
                return None
            verify_cache(expected["cache"], claim, app.state.chat_signing_key)
        elif claim.get("correction") is not None:
            return None
        return row

    @app.post("/internal/chat/v2/attempts")
    async def attempt(request: Request):
        if not getattr(app.state, "chat_prompt_version", None):
            return signed_response(request, {"code": "chat_not_ready"}, 503)
        try:
            capacity = validate_capacity(getattr(app.state, "chat_capacity", 8))
        except StartupError:
            return signed_response(request, {"code": "capacity_invalid"}, 503)
        resources = getattr(app.state, "chat_resources", None)
        if os.getenv("CHAT_ENABLED", "false").lower() == "true" and resources is None:
            return signed_response(request, {"code": "chat_not_ready"}, 503)
        try:
            claim = json.loads(request.state.chat_body)
            if not isinstance(claim, dict) or claim.get("v") != 2:
                return signed_response(request, {"code": "invalid_claim"}, 409)
            row = await asyncio.to_thread(owned, claim)
            if row is None:
                return signed_response(request, {"code": "claim_not_current"}, 404)
        except Exception:
            return signed_response(request, {"code": "claim_unavailable"}, 409)
        if resources is not None:
            from app.core.chat_resources import TokenBudgetExceeded

            try:
                await asyncio.to_thread(resources.validate_context, claim["context"])
                if claim.get("correction"):
                    await asyncio.to_thread(resources.validate_correction, claim["context"], claim["correction"])
            except TokenBudgetExceeded:
                return signed_response(request, {"code": "context_token_limit"}, 413)
            except Exception:
                return signed_response(
                    request, {"code": "context_contract_invalid"}, 409
                )
        gateway = getattr(app.state, "chat_gateway", None)
        if gateway is None:
            try:
                from app.clients.chat_gateway import configured_gateway

                gateway = configured_gateway()
            except Exception:
                gateway = None
        if gateway is None:
            return signed_response(request, {"code": "chat_not_ready"}, 503)
        if resources is not None:
            from app.clients.mock_chat import MockChatGateway

            if (claim["context"]["tool_protocol"] == "mock-direct-v1") != isinstance(
                gateway, MockChatGateway
            ):
                return signed_response(request, {"code": "tool_protocol_mismatch"}, 409)
        key = (claim["boot_id"], claim["attempt_id"])
        with app.state.chat_gate:
            attempts = app.state.chat_attempts
            for old in [
                old
                for old, entry in attempts.items()
                if entry["deadline"] <= time.time() and entry["task"] is None
            ]:
                del attempts[old]
            if key in attempts:
                return signed_response(
                    request, {"code": "attempt_already_dispatched"}, 409
                )
            from app.core.chat_admission import main_allowed

            if len(attempts) >= 4096 or not main_allowed(app, capacity):
                return signed_response(request, {"code": "capacity_unavailable"}, 503)
            attempts[key] = {
                "deadline": claim["deadline"] + 30,
                "task": True,
                "claim": claim,
                "tool_future": None,
                "tool_consumed": False,
            }

        async def tool_result(assistant):
            entry = app.state.chat_attempts[key]
            if entry.get("assistant") != assistant or entry["tool_future"] is None:
                raise ValueError("Unknown pending tool.")
            result = await asyncio.wait_for(
                asyncio.shield(entry["tool_future"]),
                max(0.001, claim["deadline"] - time.time() - 5),
            )
            if (
                await asyncio.to_thread(owned, claim) is None
                or time.time() >= claim["deadline"] - 5
            ):
                raise ValueError("Tool claim no longer current.")
            return result

        async def monitored_gateway():
            from app.clients.chat_gateway import diagnostic_scope

            with diagnostic_scope(claim.get("operation_id"), claim.get("attempt_id")):
                options = (
                    {"tool_result": tool_result}
                    if getattr(gateway, "requires_tool_result", False)
                    and claim["context"].get("tool_protocol")
                    == "server-documentation-v4"
                    else {}
                )
                if claim.get("correction"):
                    options["correction"] = claim["correction"]
                iterator = gateway(
                    claim["context"], claim["deadline"], **options
                ).__aiter__()
                pending = None
                try:
                    while True:
                        pending = asyncio.create_task(iterator.__anext__())
                        while True:
                            done, _ = await asyncio.wait({pending}, timeout=0.5)
                            if await asyncio.to_thread(owned, claim) is None:
                                return
                            if done:
                                break
                        try:
                            record = pending.result()
                        except StopAsyncIteration:
                            return
                        pending = None
                        yield record
                finally:
                    if pending is not None:
                        pending.cancel()
                        await asyncio.gather(pending, return_exceptions=True)
                    await iterator.aclose()

        async def stream():
            app.state.chat_attempts[key]["task"] = asyncio.current_task()
            try:
                async with asyncio.timeout(
                    max(0.001, claim["deadline"] - time.time() - 5)
                ):
                    async with aclosing(monitored_gateway()) as records:
                        async for record in records:
                            if await asyncio.to_thread(owned, claim) is None:
                                return
                            kind = record.get("type")
                            if kind == "candidate":
                                raw = encode(record["result"])
                                if len(raw) > 1024 * 1024:
                                    raise ValueError("Candidate limit.")
                                offset = 0
                                while offset < len(raw):
                                    end = min(offset + 8192, len(raw))
                                    while end > offset:
                                        try:
                                            fragment = raw[offset:end].decode("utf-8")
                                            break
                                        except UnicodeDecodeError:
                                            end -= 1
                                    yield encode(
                                        {
                                            "v": 2,
                                            "type": "candidate_chunk",
                                            "offset": offset,
                                            "text": fragment,
                                        }
                                    ) + b"\n"
                                    offset = end
                                yield encode(
                                    {
                                        "v": 2,
                                        "type": "candidate_end",
                                        "size": len(raw),
                                        "sha256": hashlib.sha256(raw).hexdigest(),
                                        "finish_reason": record.get("finish_reason"),
                                        "usage": record.get("usage"),
                                    }
                                ) + b"\n"
                                return
                            elif kind == "tool_call":
                                from app.core.chat_resources import validate_search_call

                                validate_search_call(record.get("assistant"))
                                entry = app.state.chat_attempts[key]
                                if (
                                    claim["context"].get("tool_protocol")
                                    != "server-documentation-v4"
                                    or entry["tool_future"] is not None
                                ):
                                    raise ValueError("Unexpected tool call.")
                                entry["assistant"] = record["assistant"]
                                entry["tool_future"] = (
                                    asyncio.get_running_loop().create_future()
                                )
                                yield encode(
                                    {
                                        "v": 2,
                                        "type": "tool_call",
                                        "assistant": record["assistant"],
                                    }
                                ) + b"\n"
                            elif kind == "delta":
                                if (
                                    not isinstance(record.get("text"), str)
                                    or len(record["text"].encode()) > 8192
                                ):
                                    raise ValueError("Delta limit.")
                                yield encode(
                                    {"v": 2, "type": "delta", "text": record["text"]}
                                ) + b"\n"
                            elif kind == "error":
                                yield encode(
                                    {
                                        "v": 2,
                                        "type": "error",
                                        "status": record.get("status"),
                                        "category": record.get("category"),
                                        "retry_after": record.get("retry_after"),
                                        "rule_code": record.get("rule_code"),
                                        "usage": record.get("usage"),
                                    }
                                ) + b"\n"
                                return
                            else:
                                raise ValueError("Stream record.")
            except (TimeoutError, OSError):
                yield encode({"v": 2, "type": "error", "category": "transport"}) + b"\n"
            except asyncio.CancelledError:
                raise
            except Exception:
                yield encode(
                    {
                        "v": 2,
                        "type": "error",
                        "status": 502,
                        "category": "invalid_private_response",
                    }
                ) + b"\n"
            finally:
                entry = app.state.chat_attempts[key]
                entry["task"] = None
                if entry["tool_future"] is not None and not entry["tool_future"].done():
                    entry["tool_future"].cancel()

        return StreamingResponse(
            stream(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-store"},
        )

    @app.post("/internal/chat/v2/attempts/{attempt_id}/tool-result")
    async def accept_tool_result(attempt_id: str, request: Request):
        try:
            envelope = json.loads(request.state.chat_body)
            if (
                not isinstance(envelope, dict)
                or set(envelope) != {"v", "claim", "tool_result"}
                or envelope["v"] != 2
            ):
                return signed_response(request, {"code": "invalid_tool_result"}, 409)
            claim = envelope["claim"]
            if (
                not isinstance(claim, dict)
                or claim.get("attempt_id") != attempt_id
                or await asyncio.to_thread(owned, claim) is None
            ):
                return signed_response(request, {"code": "claim_not_current"}, 404)
            entry = app.state.chat_attempts.get((claim["boot_id"], attempt_id))
            if (
                entry is None
                or entry["task"] in (None, True)
                or encode(entry["claim"]) != encode(claim)
                or entry["tool_future"] is None
                or entry["tool_consumed"]
                or entry["tool_future"].done()
                or time.time() >= claim["deadline"] - 5
            ):
                return signed_response(request, {"code": "tool_not_pending"}, 409)
            result = envelope["tool_result"]
            from app.core.chat_resources import continuation_messages

            resources = getattr(app.state, "chat_resources", None)
            if resources is None:
                if os.getenv("CHAT_ENABLED", "false").lower() == "true":
                    raise ValueError("Resources unavailable.")
                continuation_messages(claim["context"], entry["assistant"], result)
            else:
                resources.validate_tool_result(
                    claim["context"], entry["assistant"], result
                )
            if (
                await asyncio.to_thread(owned, claim) is None
                or time.time() >= claim["deadline"] - 5
            ):
                return signed_response(request, {"code": "claim_not_current"}, 404)
            if entry["tool_consumed"] or entry["tool_future"].done():
                return signed_response(request, {"code": "tool_not_pending"}, 409)
            entry["tool_consumed"] = True
            entry["tool_future"].set_result(result)
            return signed_response(
                request,
                {"v": 2, "accepted": True, "tool_call_id": result["tool_call_id"]},
            )
        except Exception:
            return signed_response(request, {"code": "invalid_tool_result"}, 409)

    @app.post("/internal/chat/v2/attempts/{attempt_id}/cancel")
    async def cancel(attempt_id: str, request: Request):
        try:
            claim = json.loads(request.state.chat_body)
            if (
                not isinstance(claim, dict)
                or claim.get("v") != 2
                or claim.get("attempt_id") != attempt_id
                or await asyncio.to_thread(owned, claim, True) is None
            ):
                return signed_response(request, {"code": "not_found"}, 404)
            with app.state.chat_gate:
                matches = [
                    entry["task"]
                    for (_, attempt_id), entry in app.state.chat_attempts.items()
                    if attempt_id == claim["attempt_id"]
                    and entry["task"] not in (None, True)
                ]
            for task in matches:
                task.cancel()
            return signed_response(request, {"v": 2, "cancelled": True})
        except Exception:
            return signed_response(request, {"code": "cancel_unavailable"}, 409)

    from app.summary import install_routes as install_summary_routes

    install_summary_routes(app, signed_response)
    return app
