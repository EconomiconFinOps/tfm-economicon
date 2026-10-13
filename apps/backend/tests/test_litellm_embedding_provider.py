"""JUP-022: LiteLLM query embedding provider of the backend, against a local fake gateway (no network)."""
import json
import time
import math
import socket
import threading
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.services import embedding_provider as module
from app.services.embedding_provider import LiteLLMEmbeddingProvider, MockEmbeddingProvider, ProviderError
from embedding_support import FakeGateway, RawServer, WordEmbeddingProvider, headers_trickling, trickle, vector_payload

KEY = "sk-backend-sentinel-0123456789"
VECTOR = [0.5] * 1536


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(module, "_sleep", lambda seconds: None)


def settings(url, retries=2, timeout=2.0, model="economicon-embedding", dimension=1536):
    return SimpleNamespace(
        litellm_base_url=url, litellm_api_key=SecretStr(KEY), embedding_model=model,
        embedding_dimension=dimension, embedding_timeout_seconds=timeout, embedding_max_retries=retries,
    )


def provider_for(gateway, **kwargs):
    return LiteLLMEmbeddingProvider(settings(gateway.url, **kwargs))


def test_embeds_the_question_with_the_alias_and_the_key_of_the_backend():
    with FakeGateway((200, vector_payload(VECTOR))) as gateway:
        provider = provider_for(gateway)
        result = provider.embed("¿Qué semáforo tiene un 5 %?")
    assert result == VECTOR and len(result) == 1536
    request = gateway.requests[0]
    assert request["path"] == "/v1/embeddings"
    assert request["authorization"] == "Bearer " + KEY
    assert request["body"] == {"model": "economicon-embedding", "input": "¿Qué semáforo tiene un 5 %?", "dimensions": 1536}
    assert provider.name == "litellm" and provider.dimension == 1536


def test_base_url_without_v1_suffix_is_completed():
    with FakeGateway((200, vector_payload(VECTOR))) as gateway:
        LiteLLMEmbeddingProvider(settings(gateway.url[: -len("/v1")])).embed("x")
    assert gateway.requests[0]["path"] == "/v1/embeddings"


@pytest.mark.parametrize("payload", [
    vector_payload([0.1] * 1535),
    vector_payload([0.1] * 1537),
    vector_payload([0.1] * 1535 + [None]),
    vector_payload([0.1] * 1535 + ["0.1"]),
    vector_payload([0.1] * 1535 + [True]),
    vector_payload(VECTOR, VECTOR),
    {"data": []},
    {"data": [{}]},
    {"data": "x"},
    {"other": 1},
    [],
])
def test_wrong_shapes_are_reported_as_invalid_responses(payload):
    with FakeGateway((200, payload)) as gateway:
        with pytest.raises(ProviderError) as error:
            provider_for(gateway).embed("x")
    assert error.value.category == "invalid_response"


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity", "1e999", "-1e999"])
def test_non_finite_values_are_rejected(literal):
    body = ('{"data":[{"embedding":[' + ",".join([literal] + ["0.1"] * 1535) + "]}]}").encode()
    with FakeGateway((200, body)) as gateway:
        with pytest.raises(ProviderError) as error:
            provider_for(gateway).embed("x")
    assert error.value.category == "invalid_response"


def test_non_json_body_is_an_invalid_response():
    with FakeGateway((200, b"<html>no</html>")) as gateway:
        with pytest.raises(ProviderError) as error:
            provider_for(gateway).embed("x")
    assert error.value.category == "invalid_response"


@pytest.mark.parametrize("status", [429, 503, 502])
def test_transient_statuses_are_retried_a_bounded_number_of_times(status):
    with FakeGateway((status, {"error": "busy"})) as gateway:
        with pytest.raises(ProviderError) as error:
            provider_for(gateway, retries=2).embed("x")
    assert len(gateway.requests) == 3
    assert error.value.category == ("rate_limit" if status == 429 else "upstream")


def test_a_transient_failure_followed_by_success_is_recovered():
    with FakeGateway((503, {}), (200, vector_payload(VECTOR))) as gateway:
        assert provider_for(gateway).embed("x") == VECTOR
    assert len(gateway.requests) == 2


@pytest.mark.parametrize("status,category", [(401, "authentication"), (403, "authentication"), (400, "request"), (404, "request")])
def test_non_transient_statuses_are_not_retried(status, category):
    with FakeGateway((status, {"error": "no"})) as gateway:
        with pytest.raises(ProviderError) as error:
            provider_for(gateway, retries=5).embed("x")
    assert len(gateway.requests) == 1 and error.value.category == category


def test_zero_retries_means_one_attempt():
    with FakeGateway((503, {})) as gateway:
        with pytest.raises(ProviderError):
            provider_for(gateway, retries=0).embed("x")
    assert len(gateway.requests) == 1


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_redirects_are_not_followed_and_the_key_is_not_sent_to_the_new_location(status):
    with FakeGateway((200, vector_payload(VECTOR))) as target:
        with FakeGateway((status, {}, {"Location": target.url + "/embeddings"})) as origin:
            with pytest.raises(ProviderError) as error:
                provider_for(origin).embed("x")
    assert error.value.category == "redirect"
    assert target.requests == [] and len(origin.requests) == 1


def test_slow_gateway_ends_in_a_timeout_category():
    with FakeGateway((200, vector_payload(VECTOR), {}, 1.5)) as gateway:
        with pytest.raises(ProviderError) as error:
            provider_for(gateway, retries=0, timeout=0.2).embed("x")
    assert error.value.category == "timeout"


def test_connection_refused_is_a_connection_category():
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    with pytest.raises(ProviderError) as error:
        LiteLLMEmbeddingProvider(settings(f"http://127.0.0.1:{port}/v1", retries=0, timeout=10)).embed("x")
    assert error.value.category == "connection"


def test_slow_body_is_cut_by_an_overall_deadline():
    # The gateway sends headers and then trickles the body: a per-read timeout alone would never fire.
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    stop = threading.Event()

    def trickle():
        connection, _ = server.accept()
        connection.recv(65536)
        connection.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 100000\r\n\r\n")
        while not stop.is_set():
            try:
                connection.sendall(b"0")
            except OSError:
                break
            stop.wait(0.05)
        connection.close()

    thread = threading.Thread(target=trickle, daemon=True)
    thread.start()
    try:
        provider = LiteLLMEmbeddingProvider(settings(f"http://127.0.0.1:{server.getsockname()[1]}/v1", retries=0, timeout=0.5))
        outcome = []

        def call():
            try:
                provider.embed("x")
            except ProviderError as exc:
                outcome.append(exc.category)

        caller = threading.Thread(target=call, daemon=True)
        caller.start()
        caller.join(timeout=8)
        assert not caller.is_alive(), "the call outlived its overall deadline"
        assert outcome == ["timeout"]
    finally:
        stop.set()
        server.close()


def test_errors_and_repr_never_contain_the_key_or_upstream_text():
    with FakeGateway((401, {"error": "bad key " + KEY})) as gateway:
        provider = provider_for(gateway)
        with pytest.raises(ProviderError) as error:
            provider.embed("x")
    for text in (str(error.value), repr(error.value), repr(provider), str(provider.__dict__)):
        assert KEY not in text and KEY[:12] not in text


def test_a_gateway_that_echoes_the_key_in_a_valid_response_does_not_leak_it_either():
    with FakeGateway((200, {"data": [{"embedding": VECTOR}], "echo": KEY})) as gateway:
        assert provider_for(gateway).embed("x") == VECTOR


def test_categories_are_the_fixed_set_of_the_processor_client():
    assert {"timeout", "connection", "transport", "authentication", "request", "redirect",
            "rate_limit", "upstream", "invalid_response"} == module.PROVIDER_ERROR_CATEGORIES
    assert ProviderError("anything-else").category == "transport"


def test_provider_contract_matches_the_mock_provider():
    mock = MockEmbeddingProvider(8)
    assert hasattr(mock, "name") and mock.name == "mock" and mock.dimension == 8
    with FakeGateway((200, vector_payload(VECTOR))) as gateway:
        real = provider_for(gateway)
    assert real.dimension == 1536 and callable(real.embed)


def test_word_provider_is_deterministic_and_shared_words_are_closer():
    provider = WordEmbeddingProvider()
    assert provider.embed("coste no asignado") == provider.embed("coste no asignado")

    def distance(left, right):
        a, b = provider.embed(left), provider.embed(right)
        return 1 - sum(x * y for x, y in zip(a, b))

    assert distance("coste no asignado semaforo", "semaforo del coste no asignado") < distance("coste no asignado semaforo", "reserva de maquinas virtuales")
    assert all(math.isfinite(value) for value in provider.embed("hola mundo"))


def test_proxy_settings_of_the_environment_are_ignored_so_the_key_never_goes_through_a_proxy(monkeypatch):
    with FakeGateway((200, vector_payload(VECTOR))) as proxy:
        monkeypatch.setenv("HTTP_PROXY", proxy.url.replace("/v1", ""))
        monkeypatch.setenv("http_proxy", proxy.url.replace("/v1", ""))
        monkeypatch.delenv("NO_PROXY", raising=False)
        monkeypatch.delenv("no_proxy", raising=False)
        with FakeGateway((200, vector_payload(VECTOR))) as gateway:
            assert provider_for(gateway).embed("x") == VECTOR
    assert proxy.requests == [] and len(gateway.requests) == 1


def timed_embed(url, timeout, retries):
    provider = LiteLLMEmbeddingProvider(settings(url, retries=retries, timeout=timeout))
    outcome = []
    started = time.monotonic()

    def call():
        try:
            provider.embed("x")
            outcome.append("ok")
        except ProviderError as exc:
            outcome.append(exc.category)

    caller = threading.Thread(target=call, daemon=True)
    caller.start()
    caller.join(timeout=15)
    assert not caller.is_alive(), "the call outlived any reasonable deadline"
    return outcome[0], time.monotonic() - started


@pytest.mark.parametrize("timeout,retries,limit", [(0.05, 0, 0.45), (0.5, 0, 1.0), (0.1, 2, 1.6)])
def test_slow_headers_are_cut_by_the_overall_deadline_of_each_attempt(timeout, retries, limit):
    with RawServer(headers_trickling) as server:
        category, elapsed = timed_embed(server.url, timeout, retries)
        hits = server.hits
    assert category == "timeout"
    assert elapsed < limit, f"{elapsed:.3f}s"
    assert hits == retries + 1


def test_a_status_line_that_trickles_is_also_bounded():
    full = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}"
    with RawServer(trickle(full, 0.03)) as server:
        category, elapsed = timed_embed(server.url, 0.2, 0)
    assert category == "timeout" and elapsed < 0.6


def test_a_server_that_accepts_and_never_answers_ends_in_a_timeout():
    with RawServer(lambda connection: time.sleep(3)) as server:
        category, elapsed = timed_embed(server.url, 0.3, 0)
    assert category == "timeout" and elapsed < 0.8


def test_a_body_that_stops_midway_ends_in_a_timeout():
    def stalls(connection):
        connection.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 500\r\n\r\n12345")
        time.sleep(3)

    with RawServer(stalls) as server:
        category, elapsed = timed_embed(server.url, 0.3, 0)
    assert category == "timeout" and elapsed < 0.8


def test_a_slow_body_is_a_timeout_and_not_another_category_whatever_the_timeout_value():
    payload = b'{"data":[{"embedding":[' + b"0.1," * 40 + b"0.1]}]}"
    head = b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(payload)).encode() + b"\r\n\r\n"

    def slow(connection):
        connection.sendall(head)
        trickle(payload, 0.03)(connection)

    with RawServer(slow) as server:
        category, elapsed = timed_embed(server.url, 0.5, 0)
    assert category == "timeout" and elapsed < 1.0


def test_the_normal_response_still_works_with_chunked_transfer_encoding():
    body = json.dumps(vector_payload(VECTOR)).encode()
    raw = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nTransfer-Encoding: chunked\r\n\r\n" + hex(len(body))[2:].encode() + b"\r\n" + body + b"\r\n0\r\n\r\n"
    with RawServer(lambda connection: connection.sendall(raw)) as server:
        assert LiteLLMEmbeddingProvider(settings(server.url)).embed("x") == VECTOR


def test_a_stall_after_late_headers_still_ends_at_the_attempt_deadline():
    # Headers arrive late and then nothing: the wait for the rest must use the time left, not a fresh timeout.
    def late_then_silent(connection):
        time.sleep(0.35)
        connection.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 500\r\n\r\n12345")
        time.sleep(3)

    with RawServer(late_then_silent) as server:
        category, elapsed = timed_embed(server.url, 0.6, 0)
    assert category == "timeout" and elapsed < 0.8, f"{elapsed:.3f}s"


def test_the_connection_is_opened_with_the_time_left_of_the_attempt(monkeypatch):
    seen = []

    class Recording(socket.socket):
        def connect(self, address):
            seen.append(self.gettimeout())
            return super().connect(address)

    with FakeGateway((200, vector_payload(VECTOR))) as gateway:
        provider = provider_for(gateway, timeout=2.0)
        monkeypatch.setattr(socket, "socket", Recording)
        assert provider.embed("x") == VECTOR
    assert len(seen) == 1 and seen[0] is not None and 0 < seen[0] <= 2.0
