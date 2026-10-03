"""JUP-022: sanitized 503 failures, query vector verification and provider compatibility of the retrieval."""
import json
import logging
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from app.api.routes.assistant import RETRIEVAL_UNAVAILABLE, send_message
from app.schemas.assistant import MessageCreateRequest
from app.services.assistant import AssistantService
from app.services.embedding_provider import ProviderError
from app.services.vector_store import EmbeddingDimensionMismatch, PgVectorQueryStore
from test_retrieval_contract import Database, RecordingEngine, row, store_with

QUESTION = "frase-secreta-de-la-pregunta"
UPSTREAM_TEXT = "texto-interno-del-upstream"


class Failing:
    name = "mock"
    dimension = 3

    def __init__(self, error):
        self.error = error

    def embed(self, text):
        raise self.error


class GoodEmbedding:
    name = "mock"
    dimension = 3

    def __init__(self, vector=(0.1, 0.2, 0.3)):
        self.vector = list(vector)

    def embed(self, text):
        return self.vector


class Store:
    def __init__(self, error=None, result=()):
        self.error, self.result, self.calls = error, list(result), []

    def search_chunks(self, tenant_id, query_embedding, top_k, max_distance, provider=None):
        self.calls.append((tenant_id, provider))
        if self.error:
            raise self.error
        return self.result


class RecordingDatabase(Database):
    def __init__(self):
        self.messages = []

    def append_message(self, **kwargs):
        self.messages.append(kwargs["role"])
        return super().append_message(**kwargs)


def ask(embedding, store, database=None):
    return send_message(
        conversation_id="c1", payload=MessageCreateRequest(content=QUESTION),
        current_user={"id": "u"}, tenant_id="tenant-a", database=database or RecordingDatabase(),
        vector_store=store, embedding_provider=embedding, assistant_service=AssistantService(),
    )


def failure_of(embedding, store):
    with pytest.raises(HTTPException) as error:
        ask(embedding, store)
    return error.value


def assert_fixed(error):
    assert error.status_code == 503
    assert error.detail == RETRIEVAL_UNAVAILABLE
    text = json.dumps(error.detail) + str(error.headers)
    assert QUESTION not in text and UPSTREAM_TEXT not in text


@pytest.mark.parametrize("category", ["timeout", "authentication", "rate_limit", "upstream", "connection", "invalid_response", "redirect", "request", "transport"])
def test_every_provider_failure_gives_the_same_fixed_503(category):
    assert_fixed(failure_of(Failing(ProviderError(category)), Store()))


def test_provider_failure_with_an_empty_tenant_is_a_503_and_not_the_no_context_answer():
    error = failure_of(Failing(ProviderError("timeout")), Store(result=[]))
    assert_fixed(error)


def test_vector_store_failure_gives_the_same_fixed_503_without_database_text():
    database_error = OperationalError("SELECT secret FROM t", {"p": QUESTION}, Exception(UPSTREAM_TEXT + " password=hunter2"))
    error = failure_of(GoodEmbedding(), Store(error=database_error))
    assert_fixed(error)
    assert "hunter2" not in repr(error.detail) and "SELECT" not in repr(error.detail)


def test_an_unexpected_error_in_the_provider_is_also_sanitized():
    assert_fixed(failure_of(Failing(RuntimeError(UPSTREAM_TEXT)), Store()))


def test_the_failure_category_is_logged_without_the_question_or_upstream_text(capsys):
    from app.core.logging import configure_logging

    configure_logging()
    capsys.readouterr()
    failure_of(Failing(ProviderError("authentication")), Store())
    failure_of(GoodEmbedding(), Store(error=OperationalError("s", {}, Exception(UPSTREAM_TEXT))))
    output = capsys.readouterr().out
    events = [json.loads(line) for line in output.splitlines() if line.startswith("{")]
    failures = [event for event in events if event.get("event") == "retrieval_failed"]
    assert [event["category"] for event in failures] == ["authentication", "vector_store"]
    assert QUESTION not in output and UPSTREAM_TEXT not in output
    logging.getLogger().handlers.clear()


def test_the_user_message_is_already_stored_when_retrieval_fails():
    database = RecordingDatabase()
    with pytest.raises(HTTPException):
        ask(Failing(ProviderError("timeout")), Store(), database)
    assert database.messages == ["user"]


def test_a_question_vector_of_the_wrong_length_is_not_searched():
    store = Store()
    embedding = GoodEmbedding(vector=(0.1, 0.2))
    assert_fixed(failure_of(embedding, store))
    assert store.calls == []


@pytest.mark.parametrize("vector", [(0.1, float("nan"), 0.3), (0.1, float("inf"), 0.3)])
def test_a_non_finite_question_vector_is_not_searched(vector):
    store = Store()
    assert_fixed(failure_of(GoodEmbedding(vector=vector), store))
    assert store.calls == []


def test_the_search_is_restricted_to_vectors_of_the_configured_provider():
    store = Store(result=[])
    ask(GoodEmbedding(), store)
    assert store.calls == [("tenant-a", "mock")]


def test_the_sql_filters_by_provider_when_given_and_binds_it_as_a_parameter():
    store = store_with()
    store.search_chunks("tenant-a", [1.0], provider="litellm")
    sql, params = store.engine.executed[-1]
    assert "ce.provider = :provider" in sql and params["provider"] == "litellm"
    store.search_chunks("tenant-a", [1.0])
    sql, params = store.engine.executed[-1]
    assert "provider" not in sql.split("WHERE", 1)[1] and "provider" not in params


# Startup comparison of the column dimension with the provider dimension.

class ColumnEngine(RecordingEngine):
    def __init__(self, column):
        super().__init__()
        self.column = column

    def execute(self, statement, params=None):
        self.executed.append((" ".join(str(statement).split()), dict(params or {})))
        return SimpleNamespace(scalar=lambda: self.column)


def store_with_column(column):
    store = PgVectorQueryStore.__new__(PgVectorQueryStore)
    store.engine = ColumnEngine(column)
    return store


@pytest.mark.parametrize("column,provider", [(8, 1536), (1536, 8)])
def test_a_column_with_another_dimension_stops_startup_with_a_fixed_message(column, provider):
    with pytest.raises(EmbeddingDimensionMismatch) as error:
        store_with_column(column).verify_dimension(provider)
    message = str(error.value)
    assert "re-index" in message and str(column) not in message and str(provider) not in message


def test_a_matching_column_or_a_missing_table_passes_the_startup_check():
    store_with_column(1536).verify_dimension(1536)
    store_with_column(None).verify_dimension(1536)


@pytest.mark.parametrize("vector", [(0.0, 0.0, 0.0), (1e-9, -1e-9, 0.0), (0.0, 4e-7, 0.0)])
def test_a_question_vector_without_direction_is_not_searched(vector):
    store = Store()
    assert_fixed(failure_of(GoodEmbedding(vector=vector), store))
    assert store.calls == []


def test_a_vector_with_a_single_usable_component_is_searched():
    store = Store(result=[])
    ask(GoodEmbedding(vector=(0.0, 0.00001, 0.0)), store)
    assert len(store.calls) == 1
