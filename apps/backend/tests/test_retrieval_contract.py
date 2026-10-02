"""JUP-022: retrieval contract of PgVectorQueryStore and its use by the chat route.

The SQL is checked against a recording engine; the ordering, the threshold and the tenant
filter over real vectors are covered by test_retrieval_contract_pgvector.py (opt-in).
"""
import re
from types import SimpleNamespace

import pytest

from app.api.routes.assistant import send_message
from app.schemas.assistant import MessageCreateRequest
from app.services.assistant import AssistantService
from app.services.vector_store import PgVectorQueryStore


class RecordingEngine:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.executed = []
        self.connected = 0

    def connect(self):
        self.connected += 1
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, statement, params):
        self.executed.append((" ".join(str(statement).split()), dict(params)))
        return iter(self.rows)


def store_with(rows=()):
    store = PgVectorQueryStore.__new__(PgVectorQueryStore)
    store.engine = RecordingEngine(rows)
    return store


def row(chunk_id, distance, source="doc", content="text"):
    return SimpleNamespace(chunk_id=chunk_id, source=source, content=content, distance=distance)


def last(store):
    return store.engine.executed[-1]


# Current behaviour that must not change by accident (task 1.2).

def test_default_returns_the_four_closest_without_threshold():
    store = store_with([row("c1", 0.1)])
    store.search_chunks("tenant-a", [1.0, 0.0])
    sql, params = last(store)
    assert params["top_k"] == 4
    assert "max_distance" not in params
    assert "<=>" in sql and "LIMIT :top_k" in sql


def test_tenant_filter_is_part_of_the_same_statement_as_the_ranking():
    store = store_with()
    store.search_chunks("tenant-a", [1.0, 0.0])
    sql, params = last(store)
    assert "kd.tenant_id = :tenant_id" in sql and params["tenant_id"] == "tenant-a"
    assert len(store.engine.executed) == 1


def test_query_vector_is_sent_as_a_pgvector_literal():
    store = store_with()
    store.search_chunks("tenant-a", [1.0, 0.5, -0.25])
    assert last(store)[1]["query_embedding"] == "[1.000000,0.500000,-0.250000]"


def test_rows_are_mapped_in_the_order_returned_by_the_database():
    store = store_with([row("b", 0.2, "s1", "x"), row("a", 0.2, "s2", "y")])
    result = store.search_chunks("tenant-a", [1.0])
    assert result == [
        {"chunk_id": "b", "source": "s1", "content": "x", "distance": 0.2},
        {"chunk_id": "a", "source": "s2", "content": "y", "distance": 0.2},
    ]


# Deterministic ordering, threshold and parameters.

def test_ordering_is_distance_then_chunk_identifier():
    store = store_with()
    store.search_chunks("tenant-a", [1.0])
    sql = last(store)[0]
    assert re.search(r"ORDER BY (distance|ranked\.distance|\(ce\.embedding <=> [^)]+\)(?: AS distance)?), (chunk_id|ranked\.chunk_id|dc\.id)\b", sql), sql
    assert "DESC" not in sql


def test_threshold_is_applied_with_less_than_or_equal_only_when_defined():
    store = store_with()
    store.search_chunks("tenant-a", [1.0], top_k=3, max_distance=0.5)
    sql, params = last(store)
    assert params["max_distance"] == 0.5 and params["top_k"] == 3
    assert "distance <= :max_distance" in sql
    store.search_chunks("tenant-a", [1.0], top_k=3)
    sql, params = last(store)
    assert "max_distance" not in sql and "max_distance" not in params


def test_threshold_filters_before_the_limit():
    store = store_with()
    store.search_chunks("tenant-a", [1.0], max_distance=0.5)
    sql = last(store)[0]
    assert sql.index("distance <= :max_distance") < sql.index("LIMIT :top_k")


@pytest.mark.parametrize("top_k", [0, -1, 21, 2.5, "4", True, None])
def test_invalid_top_k_is_rejected_before_connecting(top_k):
    store = store_with()
    with pytest.raises(ValueError, match="top_k"):
        store.search_chunks("tenant-a", [1.0], top_k=top_k)
    assert store.engine.connected == 0


@pytest.mark.parametrize("value", [0, -0.1, 2.0001, float("nan"), float("inf"), "0.5", True])
def test_invalid_max_distance_is_rejected_before_connecting(value):
    store = store_with()
    with pytest.raises(ValueError, match="max_distance"):
        store.search_chunks("tenant-a", [1.0], max_distance=value)
    assert store.engine.connected == 0


@pytest.mark.parametrize("value", [0.0001, 1, 2, 2.0])
def test_valid_max_distance_values_are_accepted(value):
    store = store_with()
    store.search_chunks("tenant-a", [1.0], max_distance=value)
    assert last(store)[1]["max_distance"] == float(value)


# The chat route uses the configured parameters and keeps the no-context state.

class Store:
    def __init__(self, result):
        self.result, self.calls = result, []

    def search_chunks(self, tenant_id, query_embedding, top_k, max_distance):
        self.calls.append((tenant_id, top_k, max_distance))
        return self.result


class Database:
    def fetch_conversation(self, *args):
        return {"id": "c1", "tenant_id": "t", "user_id": "u", "title": "x",
                "created_at": "2026-09-01T00:00:00Z", "updated_at": "2026-09-01T00:00:00Z"}

    def append_message(self, **kwargs):
        return {"id": "m-" + kwargs["role"], "created_at": "2026-09-01T00:00:00Z", "metadata": {}, **kwargs}


class Embedding:
    def embed(self, text):
        return [0.0]


def ask(store, monkeypatch, **env):
    for name, value in env.items():
        monkeypatch.setenv(name.upper(), str(value))
    return send_message(
        conversation_id="c1", payload=MessageCreateRequest(content="pregunta"),
        current_user={"id": "u"}, tenant_id="tenant-a", database=Database(), vector_store=store,
        embedding_provider=Embedding(), assistant_service=AssistantService(),
    )


def test_route_passes_the_configured_parameters(monkeypatch):
    store = Store([])
    ask(store, monkeypatch, retrieval_top_k=6, retrieval_max_distance="0.4")
    assert store.calls == [("tenant-a", 6, 0.4)]


def test_route_defaults_keep_four_results_and_no_threshold(monkeypatch):
    store = Store([])
    ask(store, monkeypatch)
    assert store.calls == [("tenant-a", 4, None)]


def test_empty_retrieval_gives_the_no_context_answer_and_no_citations(monkeypatch):
    reply = ask(Store([]), monkeypatch)
    assert "No he encontrado contexto relevante" in reply.assistant_message.content
    assert reply.assistant_message.metadata == {"citations": []}
    assert reply.retrieved_context == []


def test_non_empty_retrieval_cites_the_returned_fragments(monkeypatch):
    chunk = {"chunk_id": "c-9", "source": "rules", "content": "Umbral del 5 %", "distance": 0.2}
    reply = ask(Store([chunk]), monkeypatch)
    assert reply.assistant_message.metadata == {"citations": ["c-9"]}
    assert [item.chunk_id for item in reply.retrieved_context] == ["c-9"]
