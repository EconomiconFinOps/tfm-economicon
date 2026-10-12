"""Signed summary RPC, single dispatch and explicit uncertain-outcome recovery."""

import asyncio
import hashlib
import hmac
import http.client
import json
import socket
import threading
import time
from uuid import UUID
from app.db.chat_repository import ChatError
from app.schemas.chat import canonical
from app.services.summary_validation import validate_output
from app.core.config import get_settings

ROOT = "/internal/chat/v2/summaries"


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key.")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("Non-finite JSON.")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


class SummaryTransport:
    def __init__(self, parent):
        self.parent = parent
        self.control = asyncio.Semaphore(4)
        self.workers = {}
        self.sent = {}
        self.connections = {}

    validate_output = staticmethod(validate_output)

    def _exchange(self, method, path, raw, headers, deadline, holder, cancelled, limit):
        remaining = deadline - time.time()
        if remaining <= 0 or cancelled.is_set():
            raise TimeoutError()
        connection = http.client.HTTPConnection(
            self.parent.host, self.parent.port, timeout=min(5, remaining)
        )
        holder["connection"] = connection
        try:
            connection.connect()
            if cancelled.is_set() or deadline <= time.time():
                raise TimeoutError()
            connection.sock.settimeout(deadline - time.time())
            connection.request(method, path, body=raw, headers=headers)
            response = connection.getresponse()
            holder["response"] = response
            data = response.read(limit + 1)
            if (
                time.time() > deadline
                or len(data) > limit
                or not response.getheader("Content-Type", "").startswith(
                    "application/json"
                )
            ):
                raise ValueError("Summary response limit or format.")
            nonce = headers["X-Chat-Nonce"]
            message = f"chat-v2-response\n{nonce}\n{response.status}\n{hashlib.sha256(data).hexdigest()}".encode()
            if response.getheader("X-Chat-Nonce") != nonce or not hmac.compare_digest(
                response.getheader("X-Chat-Signature", ""),
                hmac.new(self.parent.key, message, hashlib.sha256).hexdigest(),
            ):
                raise ValueError("Summary response signature.")
            value = strict_json(data)
            if (
                not isinstance(value, dict)
                or type(value.get("v")) is not int
                or value["v"] != 2
            ):
                raise ValueError("Summary response version.")
            return value, response.status
        finally:
            connection.close()

    @staticmethod
    def _interrupt(holder, cancelled):
        cancelled.set()
        connection = holder.get("connection")
        sock = getattr(connection, "sock", None)
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    async def _request(
        self, method, path, value, deadline, identity=None, limit=1048576
    ):
        if deadline <= time.time():
            raise ChatError(503, "summary_deadline")
        raw = b"" if value is None else canonical(value).encode()
        if len(raw) > 1048576:
            raise ChatError(413, "summary_input_limit")
        holder = {}
        cancelled = threading.Event()
        token = object()
        worker = asyncio.create_task(
            asyncio.to_thread(
                self._exchange,
                method,
                path,
                raw,
                self.parent.headers(method, path, raw),
                deadline,
                holder,
                cancelled,
                limit,
            )
        )
        self.workers[token] = worker
        self.connections[token] = (holder, cancelled)

        def done(task):
            self.workers.pop(token, None)
            self.connections.pop(token, None)
            if not task.cancelled():
                task.exception()

        worker.add_done_callback(done)
        try:
            result, status = await asyncio.wait_for(
                asyncio.shield(worker), max(0.001, deadline - time.time())
            )
            if identity is not None:
                for key in (
                    "job_id",
                    "scope",
                    "boot_id",
                    "input_hash",
                    "summary_version",
                ):
                    if result.get(key) != identity.get(key):
                        raise ValueError("Summary response identity.")
                if (
                    result.get("state")
                    not in ("running", "completed", "failed", "cancelling", "cancelled")
                    or type(result.get("settled")) is not bool
                ):
                    raise ValueError("Summary response state.")
                if result["state"] == "completed":
                    receipt = result.get("receipt")
                    if (
                        result["settled"] is not True
                        or not isinstance(receipt, dict)
                        or type(receipt.get("dispatch_count")) is not int
                        or receipt["dispatch_count"] != 1
                        or not isinstance(receipt.get("call_id"), str)
                        or not receipt["call_id"]
                        or receipt.get("input_hash") != identity["input_hash"]
                        or receipt.get("output_hash")
                        != hashlib.sha256(
                            canonical(result.get("output")).encode()
                        ).hexdigest()
                    ):
                        raise ValueError("Summary receipt.")
            if not 200 <= status < 300 and identity is None:
                raise ChatError(status, "summary_not_ready")
            return result
        except asyncio.CancelledError:
            self._interrupt(holder, cancelled)
            raise
        except ChatError:
            raise
        except Exception:
            self._interrupt(holder, cancelled)
            # Failure does not establish whether the other process dispatched.
            raise ChatError(503, "summary_outcome_unknown") from None

    async def descriptor(self):
        async with self.control:
            value = await self._request(
                "GET",
                "/internal/chat/v2/summary/descriptor",
                None,
                time.time() + 10,
                limit=16384,
            )
            if (
                not isinstance(value.get("boot_id"), str)
                or not value["boot_id"]
                or not isinstance(value.get("summary_version"), str)
                or not value["summary_version"]
            ):
                raise ChatError(503, "summary_descriptor_invalid")
            for field in (
                "manifest_sha256",
                "tokenizer_sha256",
                "response_schema_sha256",
            ):
                digest = value.get(field)
                if (
                    not isinstance(digest, str)
                    or len(digest) != 64
                    or any(c not in "0123456789abcdef" for c in digest)
                ):
                    raise ChatError(503, "summary_descriptor_invalid")
            return value

    async def submit(self, envelope):
        try:
            job = envelope["job_id"]
            assert str(UUID(job)) == job
            deadline = envelope["deadline"]
            assert (
                type(deadline) in (int, float)
                and time.time()
                < deadline
                <= time.time() + get_settings().summary_timeout_seconds
            )
        except (ValueError, KeyError, AssertionError, TypeError):
            raise ChatError(409, "summary_input_invalid") from None
        # Retain replay protection and uncertain outcomes. At capacity, defer;
        # never evict a live or uncertain job to admit a fresh dispatch.
        if job in self.sent:
            raise ChatError(409, "summary_job_replayed")
        if len(self.sent) >= 4096:
            raise ChatError(503, "summary_transport_capacity")
        self.sent[job] = envelope["input_hash"]
        return await self._request("POST", ROOT, envelope, deadline, identity=envelope)

    async def _control(self, envelope, cancel):
        job = envelope["job_id"]
        try:
            if str(UUID(job)) != job:
                raise ValueError()
        except (ValueError, TypeError):
            raise ChatError(404, "not_found") from None
        body = {key: envelope[key] for key in ("scope", "boot_id", "input_hash")}
        body["v"] = 2
        async with self.control:
            return await self._request(
                "POST" if cancel else "GET",
                ROOT + "/" + job + ("/cancel" if cancel else ""),
                body,
                time.time() + 2,
                identity=envelope,
            )

    async def status(self, envelope):
        return await self._control(envelope, False)

    async def cancel(self, envelope):
        return await self._control(envelope, True)

    async def close(self):
        for holder, cancelled in list(self.connections.values()):
            self._interrupt(holder, cancelled)
        await asyncio.gather(*list(self.workers.values()), return_exceptions=True)
