"""Real socket waits: cancellation must not depend on cross-thread shutdown."""
from concurrent.futures import ThreadPoolExecutor
import io
import socket
import threading
import time

import pytest

from app.clients.litellm import _AttemptDeadline
from app.clients.summary_gateway import _SummaryReader, SummaryGatewayError


def test_summary_read_recovers_after_multiple_poll_timeouts():
    client, server = socket.socketpair()
    reader = io.BufferedReader(_SummaryReader(client, _AttemptDeadline(3), threading.Event()))
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(reader.read)
            time.sleep(.25)
            assert not result.done()
            server.sendall('inicio 😀'.encode())
            time.sleep(.15)
            server.sendall(' fin'.encode())
            server.shutdown(socket.SHUT_WR)
            assert result.result(timeout=2) == 'inicio 😀 fin'.encode()
    finally:
        reader.close(); client.close(); server.close()


@pytest.mark.parametrize('prefix', [b'', b'HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\npartial'])
def test_summary_read_cancel_without_socket_shutdown_preserves_other_socket(prefix):
    client, server = socket.socketpair()
    other_client, other_server = socket.socketpair()
    cancelled = threading.Event()
    reader = io.BufferedReader(_SummaryReader(client, _AttemptDeadline(3), cancelled))
    other = io.BufferedReader(_SummaryReader(other_client, _AttemptDeadline(3), threading.Event()))
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            if prefix: server.sendall(prefix)
            result = pool.submit(reader.read)
            time.sleep(.15)
            assert not result.done()
            cancelled.set()
            with pytest.raises(SummaryGatewayError) as failure:
                result.result(timeout=1)
            assert failure.value.code == 'summary_cancelled'
            other_server.sendall(b'unaffected')
            other_server.shutdown(socket.SHUT_WR)
            assert other.read() == b'unaffected'
    finally:
        reader.close(); other.close()
        for endpoint in (client, server, other_client, other_server): endpoint.close()


def test_summary_read_polling_does_not_extend_absolute_deadline():
    client, server = socket.socketpair()
    reader = io.BufferedReader(_SummaryReader(client, _AttemptDeadline(.25), threading.Event()))
    start = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            reader.read(1)
        assert time.monotonic() - start < 1
    finally:
        reader.close(); client.close(); server.close()
