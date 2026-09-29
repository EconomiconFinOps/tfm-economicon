"""Reject incompatible writes before opening a transaction or deleting chunks."""
from unittest.mock import Mock

import pytest

from app.vector_store.pgvector_store import PgVectorStore


@pytest.mark.parametrize("dimension", [0, -1])
def test_invalid_dimension_rejected_without_connecting(dimension):
    with pytest.raises(ValueError, match="greater than zero"):
        PgVectorStore("not-a-database-url", dimension)


@pytest.mark.parametrize("vectors", [[[1.0]], [[1.0] * 8, [1.0] * 9]])
def test_bad_batch_never_begins_replacement(vectors):
    store = PgVectorStore("sqlite://", 8)
    store.engine.dispose()
    store.engine = Mock()
    with pytest.raises(ValueError, match="configured dimension"):
        store.store_document(
            job_id="existing", tenant_id="tenant-a", source="test", artifact_uri=None,
            text_content="replacement", chunks=["chunk"] * len(vectors),
            embeddings=vectors, provider_name="mock",
        )
    store.engine.begin.assert_not_called()
