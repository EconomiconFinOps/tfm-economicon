"""JUP-022: one structured event per retrieval and bounded counters, without question or fragment text."""
import json
import logging

import pytest
import structlog
from fastapi import HTTPException

from app.api.routes.assistant import send_message
from app.core import metrics
from app.core.logging import configure_logging
from app.schemas.assistant import MessageCreateRequest
from app.services.assistant import AssistantService
from app.services.embedding_provider import PROVIDER_ERROR_CATEGORIES, ProviderError
from test_retrieval_contract import Database

QUESTION = "frase-secreta-de-la-pregunta"
CONTENT = "contenido-secreto-del-fragmento"
ALLOWED_FAILURES = set(PROVIDER_ERROR_CATEGORIES) | {"vector_store"}


class Embedding:
    name = "litellm"
    alias = "economicon-embedding"
    dimension = 2

    def __init__(self, error=None):
        self.error = error

    def embed(self, text):
        if self.error:
            raise self.error
        return [0.1, 0.2]


class Store:
    def __init__(self, result=(), error=None):
        self.result, self.error = list(result), error

    def search_chunks(self, tenant_id, query_embedding, top_k, max_distance, provider=None):
        if self.error:
            raise self.error
        return self.result


def chunk(identifier, document, distance):
    return {"chunk_id": identifier, "document_id": document, "source": "rules", "content": CONTENT, "distance": distance}


def ask(embedding, store, monkeypatch=None, **env):
    return send_message(
        conversation_id="c1", payload=MessageCreateRequest(content=QUESTION),
        current_user={"id": "u"}, tenant_id="tenant-a", database=Database(), vector_store=store,
        embedding_provider=embedding, assistant_service=AssistantService(),
    )


@pytest.fixture(autouse=True)
def clean_logging():
    yield
    structlog.contextvars.clear_contextvars()
    logging.getLogger().handlers.clear()


def watch(capsys):
    # Logging is configured inside the test body so the handler writes to the stdout captured for that test.
    configure_logging()
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id="req-123")
    capsys.readouterr()

    def read():
        out = capsys.readouterr().out
        return out, [json.loads(line) for line in out.splitlines() if line.startswith("{")]

    return read


def counter_value(counter, **labels):
    return (counter.labels(**labels) if labels else counter)._value.get()


def retrieval_events(parsed):
    return [event for event in parsed if event.get("event") == "retrieval"]


def test_a_retrieval_with_results_emits_one_event_with_identifiers_and_no_content(capsys):
    events = watch(capsys)
    ask(Embedding(), Store([chunk("c-1", "d-1", 0.1234567), chunk("c-2", "d-1", 0.4)]))
    output, parsed = events()
    emitted = retrieval_events(parsed)
    assert len(emitted) == 1
    event = emitted[0]
    assert event["request_id"] == "req-123" and event["tenant_id"] == "tenant-a"
    assert event["user_message_id"] == "m-user"
    assert event["chunk_ids"] == ["c-1", "c-2"] and event["document_ids"] == ["d-1", "d-1"]
    assert event["distances"] == [0.1235, 0.4]
    assert event["results"] == 2 and event["top_k"] == 4 and event["max_distance"] is None
    assert event["provider"] == "litellm" and event["alias"] == "economicon-embedding"
    assert isinstance(event["duration_ms"], (int, float)) and event["duration_ms"] >= 0
    assert QUESTION not in output and CONTENT not in output


def test_the_event_carries_the_configured_parameters(capsys, monkeypatch):
    events = watch(capsys)
    monkeypatch.setenv("RETRIEVAL_TOP_K", "7")
    monkeypatch.setenv("RETRIEVAL_MAX_DISTANCE", "0.45")
    ask(Embedding(), Store([chunk("c-1", "d-1", 0.2)]))
    event = retrieval_events(events()[1])[0]
    assert event["top_k"] == 7 and event["max_distance"] == 0.45


def test_the_stored_user_message_identifier_is_enough_to_find_the_question(capsys):
    events = watch(capsys)
    reply = ask(Embedding(), Store([chunk("c-1", "d-1", 0.2)]))
    event = retrieval_events(events()[1])[0]
    assert event["user_message_id"] == reply.user_message.id


def test_an_empty_result_is_logged_and_counted_once(capsys):
    events = watch(capsys)
    before = counter_value(metrics.retrieval_empty_total)
    ask(Embedding(), Store([]))
    event = retrieval_events(events()[1])[0]
    assert event["results"] == 0 and event["chunk_ids"] == [] and event["distances"] == []
    assert counter_value(metrics.retrieval_empty_total) == before + 1


def test_a_result_with_fragments_does_not_count_as_empty(capsys):
    events = watch(capsys)
    before = counter_value(metrics.retrieval_empty_total)
    ask(Embedding(), Store([chunk("c-1", "d-1", 0.2)]))
    assert counter_value(metrics.retrieval_empty_total) == before


@pytest.mark.parametrize("category", sorted(PROVIDER_ERROR_CATEGORIES))
def test_provider_failures_are_counted_under_their_category(capsys, category):
    events = watch(capsys)
    before = counter_value(metrics.retrieval_failures_total, category=category)
    with pytest.raises(HTTPException):
        ask(Embedding(ProviderError(category)), Store())
    assert counter_value(metrics.retrieval_failures_total, category=category) == before + 1
    output, parsed = events()
    failure = [event for event in parsed if event.get("event") == "retrieval_failed"][0]
    assert failure["category"] == category and failure["user_message_id"] == "m-user"
    assert failure["tenant_id"] == "tenant-a" and failure["provider"] == "litellm"
    assert QUESTION not in output


def test_a_store_failure_is_counted_under_vector_store(capsys):
    events = watch(capsys)
    before = counter_value(metrics.retrieval_failures_total, category="vector_store")
    with pytest.raises(HTTPException):
        ask(Embedding(), Store(error=RuntimeError("password=hunter2 " + QUESTION)))
    assert counter_value(metrics.retrieval_failures_total, category="vector_store") == before + 1
    output, _ = events()
    assert "hunter2" not in output and QUESTION not in output


def test_failure_labels_never_leave_the_fixed_set_whatever_the_upstream_says(capsys):
    events = watch(capsys)
    for message in ("boom-1", "boom-2 " + QUESTION, "boom-3 sk-secret"):
        with pytest.raises(HTTPException):
            ask(Embedding(RuntimeError(message)), Store())
        with pytest.raises(HTTPException):
            ask(Embedding(ProviderError(message)), Store())
        with pytest.raises(HTTPException):
            ask(Embedding(), Store(error=RuntimeError(message)))
    labels = {sample.labels["category"] for family in metrics.retrieval_failures_total.collect() for sample in family.samples if "category" in sample.labels}
    assert labels <= ALLOWED_FAILURES
    exposed = " ".join(line for line in metrics.generate_latest().decode().splitlines() if "backend_retrieval" in line)
    assert "backend_retrieval_failures_total" in exposed
    assert QUESTION not in exposed and "sk-secret" not in exposed and "boom" not in exposed


def test_a_failed_retrieval_does_not_emit_the_success_event(capsys):
    events = watch(capsys)
    with pytest.raises(HTTPException):
        ask(Embedding(ProviderError("timeout")), Store())
    assert retrieval_events(events()[1]) == []


def test_a_category_outside_the_fixed_set_is_counted_as_transport(capsys):
    from app.api.routes import assistant

    before = counter_value(metrics.retrieval_failures_total, category="transport")
    with pytest.raises(HTTPException):
        assistant._retrieval_failed("categoria-inventada-por-el-upstream", {"tenant_id": "t"}, 0.0)
    assert counter_value(metrics.retrieval_failures_total, category="transport") == before + 1
    labels = {sample.labels["category"] for family in metrics.retrieval_failures_total.collect() for sample in family.samples if "category" in sample.labels}
    assert "categoria-inventada-por-el-upstream" not in labels
