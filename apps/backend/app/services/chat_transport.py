"""Authenticated private HTTP; one dispatch, bounded incremental NDJSON.

Uses the standard library: no implicit retry, redirect or extra HTTP dependency.
The backend supervisor owns operation retries and the absolute attempt deadline.
"""

import asyncio
import hashlib
import hmac
import http.client
import json
import os
import time
import threading
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from app.db.chat_repository import ChatError


class PrivateChatTransport:
    def __init__(self, base, key):
        endpoint = urlsplit(base)
        if (
            endpoint.scheme != "http"
            or not endpoint.hostname
            or endpoint.username
            or endpoint.password
            or endpoint.query
            or endpoint.fragment
            or endpoint.path not in ("", "/")
        ):
            raise ChatError(503, "private_endpoint_invalid")
        if len(key) < 32:
            raise ChatError(503, "private_key_invalid")
        self.host, self.port, self.key = endpoint.hostname, endpoint.port or 8003, key
        self.control = asyncio.Semaphore(4)
        self.connections = {}
        from app.services.summary_transport import SummaryTransport

        self.summary = SummaryTransport(self)

    def headers(self, method, path, raw):
        at, nonce = str(int(time.time())), str(uuid4())
        message = f"chat-v2\n{method}\n{path}\n{at}\n{nonce}\n{hashlib.sha256(raw).hexdigest()}".encode()
        return {
            "X-Chat-Key-Id": "chat-v2",
            "X-Chat-Time": at,
            "X-Chat-Nonce": nonce,
            "X-Chat-Signature": hmac.new(self.key, message, hashlib.sha256).hexdigest(),
            "Content-Type": "application/json",
            "Connection": "close",
        }

    def _open(self, method, path, raw, headers, deadline):
        remaining = deadline - time.time()
        if remaining <= 0:
            raise TimeoutError()
        connection = http.client.HTTPConnection(
            self.host, self.port, timeout=min(5, remaining)
        )
        try:
            connection.connect()
            connection.sock.settimeout(max(0.001, deadline - time.time()))
            connection.request(method, path, body=raw, headers=headers)
            return connection, connection.getresponse()
        except BaseException:
            connection.close()
            raise

    async def descriptor(self):
        async with self.control:
            path = "/internal/chat/v2/descriptor"
            headers = self.headers("GET", path, b"")
            connection = None
            try:
                connection, response = await asyncio.to_thread(
                    self._open, "GET", path, b"", headers, time.time() + 10
                )
                raw = await asyncio.to_thread(response.read, 16385)
                signature = hmac.new(
                    self.key,
                    f"chat-v2-response\n{headers['X-Chat-Nonce']}\n{response.status}\n{hashlib.sha256(raw).hexdigest()}".encode(),
                    hashlib.sha256,
                ).hexdigest()
                if (
                    response.status != 200
                    or len(raw) > 16384
                    or response.getheader("X-Chat-Nonce") != headers["X-Chat-Nonce"]
                    or not hmac.compare_digest(
                        signature, response.getheader("X-Chat-Signature", "")
                    )
                ):
                    raise ChatError(503, "private_descriptor_invalid")
                value = json.loads(raw.decode("utf-8"))
                if (
                    value.get("v") != 2
                    or not isinstance(value.get("boot_id"), str)
                    or not value["boot_id"]
                    or not isinstance(value.get("prompt_version"), str)
                    or not value["prompt_version"]
                    or type(value.get("capacity")) is not int
                    or not 5 <= value["capacity"] <= 8
                ):
                    raise ChatError(503, "private_descriptor_invalid")
                return value
            except ChatError:
                raise
            except Exception:
                raise ChatError(503, "private_descriptor_unavailable") from None
            finally:
                if connection is not None:
                    connection.close()

    async def stream(self, claim):
        path = "/internal/chat/v2/attempts"
        raw = json.dumps(
            claim, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode()
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Private input limit.")
        connection = None
        try:
            connection, response = await asyncio.to_thread(
                self._open,
                "POST",
                path,
                raw,
                self.headers("POST", path, raw),
                claim["deadline"] - 5,
            )
            self.connections[claim["attempt_id"]] = connection
            if response.status != 200:
                yield {
                    "type": "error",
                    "status": response.status,
                    "retry_after": response.getheader("Retry-After"),
                }
                return
            if not response.getheader("Content-Type", "").startswith(
                "application/x-ndjson"
            ):
                raise ValueError("Private stream format.")
            candidate = bytearray()
            while True:
                line = await asyncio.to_thread(response.readline, 65537)
                if not line:
                    yield {"type": "error", "category": "eof"}
                    return
                if len(line) > 65536 or not line.endswith(b"\n"):
                    raise ValueError("Private frame limit or incomplete EOF.")
                record = json.loads(line.decode("utf-8"))
                if not isinstance(record, dict) or record.get("v") != 2:
                    raise ValueError("Private version.")
                kind = record.get("type")
                if kind == "candidate_chunk":
                    fragment = record.get("text")
                    if (
                        not isinstance(fragment, str)
                        or len(fragment.encode()) > 8192
                        or record.get("offset") != len(candidate)
                    ):
                        raise ValueError("Candidate chunk ordering.")
                    candidate.extend(fragment.encode())
                    if len(candidate) > 1024 * 1024:
                        raise ValueError("Candidate limit.")
                elif kind == "candidate_end":
                    if (
                        record.get("size") != len(candidate)
                        or record.get("sha256") != hashlib.sha256(candidate).hexdigest()
                    ):
                        raise ValueError("Candidate integrity.")
                    value = json.loads(candidate.decode("utf-8"))
                    yield {
                        "type": "candidate",
                        "result": value,
                        "finish_reason": record.get("finish_reason"),
                        "usage": record.get("usage"),
                    }
                    return
                elif kind in ("delta", "error", "tool_call"):
                    yield record
                    if kind == "error":
                        return
                else:
                    raise ValueError("Private record.")
        except (TimeoutError, OSError, http.client.HTTPException):
            yield {"type": "error", "category": "transport"}
        finally:
            self.connections.pop(claim["attempt_id"], None)
            if connection is not None:
                connection.close()

    async def tool_result(self, claim, result):
        path = f"/internal/chat/v2/attempts/{claim['attempt_id']}/tool-result"
        raw = json.dumps(
            {"v": 2, "claim": claim, "tool_result": result},
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Tool result body limit.")
        deadline = claim["deadline"] - 5
        headers = self.headers("POST", path, raw)
        holder = {}
        cancelled = threading.Event()
        try:
            async with self.control:
                value, status = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.summary._exchange,
                        "POST",
                        path,
                        raw,
                        headers,
                        deadline,
                        holder,
                        cancelled,
                        16384,
                    ),
                    max(0.001, deadline - time.time()),
                )
                if status != 200 or value != {
                    "v": 2,
                    "accepted": True,
                    "tool_call_id": result["tool_call_id"],
                }:
                    raise ValueError("Tool response identity.")
        finally:
            self.summary._interrupt(holder, cancelled)

    async def cancel(self, claim):
        connection = self.connections.get(claim["attempt_id"])
        if connection is not None:
            connection.close()
        path = f"/internal/chat/v2/attempts/{claim['attempt_id']}/cancel"
        raw = json.dumps({"v": 2, **claim}, separators=(",", ":")).encode()
        connection = None
        try:
            async with self.control:
                connection, _ = await asyncio.to_thread(
                    self._open,
                    "POST",
                    path,
                    raw,
                    self.headers("POST", path, raw),
                    time.time() + 2,
                )
        finally:
            if connection is not None:
                connection.close()


def configured_transport():
    base, file = os.getenv("PROCESSOR_CHAT_BASE_URL"), os.getenv(
        "CHAT_SERVICE_HMAC_KEY_FILE"
    )
    if not base or not file:
        return None
    try:
        return PrivateChatTransport(base, Path(file).read_bytes())
    except ChatError:
        raise
    except Exception:
        raise ChatError(503, "private_key_unavailable") from None
