"""JUP-022: ordering, threshold, ties and tenant filter over real pgvector (opt-in via JUP086_VECTOR_TEST_URL)."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from test_tenant_isolation_vector import retrieval  # noqa: F401  (disposable database fixture)


def add(store, chunk_id, tenant, vector, document=None, source=None, provider="mock"):
    document = document or chunk_id
    params = {"id": chunk_id, "doc": document, "tenant": tenant, "source": source or document,
              "vector": "[" + ",".join(str(value) for value in vector) + "]", "provider": provider,
              "now": datetime.now(timezone.utc)}
    with store.engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO knowledge_documents SELECT :doc, :source, :tenant, 'content', NULL, 'content', 1, :now, :now "
            "WHERE NOT EXISTS (SELECT 1 FROM knowledge_documents WHERE id = :doc)"), params)
        connection.execute(text(
            "INSERT INTO document_chunks VALUES (:id, :doc, (SELECT count(*) FROM document_chunks WHERE document_id = :doc), 'content', 7, :now)"), params)
        connection.execute(text(
            "INSERT INTO chunk_embeddings VALUES (:id, :id, CAST(:vector AS vector), 8, :provider, :now)"), params)


def axis(index, value=1.0, other=0.0):
    vector = [0.0] * 8
    vector[index] = value
    vector[(index + 1) % 8] = other
    return vector


QUERY = [1.0] + [0.0] * 7


def ids(result):
    return [item["chunk_id"] for item in result]


def test_closest_first_and_top_k_limits_the_result(retrieval):
    add(retrieval, "near", "tenant-a", [1, 0.1, 0, 0, 0, 0, 0, 0])
    add(retrieval, "mid", "tenant-a", [1, 1, 0, 0, 0, 0, 0, 0])
    add(retrieval, "far", "tenant-a", [0, 1, 0, 0, 0, 0, 0, 0])
    assert ids(retrieval.search_chunks("tenant-a", QUERY, top_k=3)) == ["near", "mid", "far"]
    result = retrieval.search_chunks("tenant-a", QUERY, top_k=2)
    assert len(result) == 2 and ids(result)[0] == "near"
    distances = [item["distance"] for item in retrieval.search_chunks("tenant-a", QUERY, top_k=20)]
    assert distances == sorted(distances)


def test_ties_are_ordered_by_chunk_identifier_inside_one_document(retrieval):
    for chunk in ("t-c", "t-a", "t-b"):
        add(retrieval, chunk, "tenant-t", [1, 1, 0, 0, 0, 0, 0, 0], document="doc-same")
    for _ in range(3):
        assert ids(retrieval.search_chunks("tenant-t", QUERY, top_k=3)) == ["t-a", "t-b", "t-c"]
    assert ids(retrieval.search_chunks("tenant-t", QUERY, top_k=2)) == ["t-a", "t-b"]


def test_ties_across_documents_follow_the_chunk_identifier_not_the_document(retrieval):
    add(retrieval, "x-2", "tenant-u", [1, 1, 0, 0, 0, 0, 0, 0], document="doc-a", source="a")
    add(retrieval, "x-1", "tenant-u", [1, 1, 0, 0, 0, 0, 0, 0], document="doc-z", source="z")
    assert ids(retrieval.search_chunks("tenant-u", QUERY, top_k=2)) == ["x-1", "x-2"]


def test_threshold_keeps_only_the_fragments_within_the_distance(retrieval):
    add(retrieval, "w-near", "tenant-w", [1, 0.05, 0, 0, 0, 0, 0, 0])
    add(retrieval, "w-far", "tenant-w", [0, 1, 0, 0, 0, 0, 0, 0])
    result = retrieval.search_chunks("tenant-w", QUERY, top_k=5, max_distance=0.1)
    assert ids(result) == ["w-near"]
    assert all(item["distance"] <= 0.1 for item in result)


def test_threshold_is_inclusive_at_the_exact_distance(retrieval):
    add(retrieval, "e-1", "tenant-e", [0, 1, 0, 0, 0, 0, 0, 0])
    distance = retrieval.search_chunks("tenant-e", QUERY)[0]["distance"]
    assert distance == pytest.approx(1.0)
    assert ids(retrieval.search_chunks("tenant-e", QUERY, max_distance=1.0)) == ["e-1"]
    assert ids(retrieval.search_chunks("tenant-e", QUERY, max_distance=0.9999)) == []


def test_top_k_larger_than_available_with_a_threshold_returns_only_the_fragments_within_it(retrieval):
    add(retrieval, "k-1", "tenant-k", [1, 0.01, 0, 0, 0, 0, 0, 0])
    add(retrieval, "k-2", "tenant-k", [0, 1, 0, 0, 0, 0, 0, 0])
    assert ids(retrieval.search_chunks("tenant-k", QUERY, top_k=20, max_distance=0.5)) == ["k-1"]


def test_result_is_empty_for_a_tenant_without_documents_and_when_all_are_beyond_the_threshold(retrieval):
    assert retrieval.search_chunks("tenant-empty", QUERY) == []
    add(retrieval, "b-1", "tenant-b2", [0, 1, 0, 0, 0, 0, 0, 0])
    assert retrieval.search_chunks("tenant-b2", QUERY, max_distance=0.5) == []


def test_a_closer_fragment_of_another_tenant_never_affects_order_or_count(retrieval):
    add(retrieval, "mine-far", "tenant-m", [0, 1, 0, 0, 0, 0, 0, 0])
    add(retrieval, "other-exact", "tenant-n", [1, 0, 0, 0, 0, 0, 0, 0])
    for kwargs in ({}, {"max_distance": 2.0}, {"max_distance": 0.01}):
        result = retrieval.search_chunks("tenant-m", QUERY, top_k=5, **kwargs)
        assert "other-exact" not in ids(result)
    assert ids(retrieval.search_chunks("tenant-m", QUERY, top_k=5)) == ["mine-far"]


def test_only_vectors_of_the_configured_provider_take_part_in_the_ranking(retrieval):
    add(retrieval, "p-mock", "tenant-p", [1, 0, 0, 0, 0, 0, 0, 0], provider="mock")
    add(retrieval, "p-real", "tenant-p", [1, 0.2, 0, 0, 0, 0, 0, 0], provider="litellm")
    assert ids(retrieval.search_chunks("tenant-p", QUERY, top_k=5, provider="litellm")) == ["p-real"]
    assert ids(retrieval.search_chunks("tenant-p", QUERY, top_k=5, provider="mock")) == ["p-mock"]
    assert ids(retrieval.search_chunks("tenant-p", QUERY, top_k=5)) == ["p-mock", "p-real"]


def test_the_stored_column_dimension_is_read_and_compared_with_the_provider(retrieval):
    from app.services.vector_store import EmbeddingDimensionMismatch

    assert retrieval.embedding_column_dimension() == 8
    retrieval.verify_dimension(8)
    with pytest.raises(EmbeddingDimensionMismatch):
        retrieval.verify_dimension(1536)
