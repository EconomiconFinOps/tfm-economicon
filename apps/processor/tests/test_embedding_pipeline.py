import json
import math

import pytest

from app.embeddings.chunker import TextChunker
from app.embeddings.providers import MockEmbeddingProvider, get_embedding_provider
from app.graphs.pipeline import PipelineRunner


class FakeAgentRuntime:
    def invoke(self, job_payload: dict, status: str) -> dict:
        return {
            "provider": "mock",
            "insight": f"Processed {job_payload['tenant_id']} with status {status}",
        }


class FakeVectorStore:
    def __init__(self):
        self.saved_payload = None

    def store_document(self, **kwargs) -> dict:
        self.saved_payload = kwargs
        return {
            "document_id": kwargs["job_id"],
            "chunk_count": len(kwargs["chunks"]),
            "embedding_count": len(kwargs["embeddings"]),
            "vector_store": "pgvector",
            "provider": kwargs["provider_name"],
        }


def test_pipeline_generates_chunks_and_embeddings():
    vector_store = FakeVectorStore()
    runner = PipelineRunner(
        FakeAgentRuntime(),
        TextChunker(chunk_size=32, chunk_overlap=8),
        MockEmbeddingProvider(dimension=8),
        vector_store,
    )

    result = runner.run(
        {
            "job_id": "job-1",
            "tenant_id": "tenant-core",
            "source": "aws-cur",
            "text_content": "This is a longer report used to validate chunk generation and embedding storage.",
            "metadata": {},
        }
    )

    assert result["embedding_result"]["chunk_count"] >= 1
    assert result["embedding_result"]["embedding_count"] == result["embedding_result"]["chunk_count"]
    assert vector_store.saved_payload["tenant_id"] == "tenant-core"
    assert len(vector_store.saved_payload["embeddings"][0]) == 8


def test_mock_embedding_provider_is_deterministic():
    provider = MockEmbeddingProvider(dimension=8)

    first = provider.embed("same chunk")
    second = provider.embed("same chunk")

    assert first == second


def test_jup023_embedding_factory_preserves_mock_signature():
    provider = get_embedding_provider("mock", 8)
    assert provider.name == "mock"
    assert provider.embed("synthetic") == MockEmbeddingProvider(8).embed("synthetic")


def test_jup023_real_embeddings_send_dimensions_and_preserve_store_identity(
    litellm_settings, gateway_transport,
):
    vector = [0.25] * 1536
    gateway_transport.responses.append((200, {"data": [{"embedding": vector}]}, {}))
    provider = get_embedding_provider("litellm", 1536, settings=litellm_settings)
    store = FakeVectorStore()
    runner = PipelineRunner(FakeAgentRuntime(), TextChunker(32, 8), provider, store)

    runner.run({"job_id": "job-1", "tenant_id": "tenant-core", "source": "azure",
                "text_content": "synthetic document", "metadata": {}})

    request, = gateway_transport.calls
    assert request.full_url == "http://gateway.invalid:4000/v1/embeddings"
    assert request.get_method() == "POST"
    assert json.loads(request.data) == {
        "model": "economicon-embedding", "input": "synthetic document", "dimensions": 1536,
    }
    assert request.get_header("Authorization") == "Bearer jup023-synthetic-virtual-key"
    assert request.timeout == 30
    assert store.saved_payload["embeddings"] == [vector]
    assert store.saved_payload["provider_name"] == provider.name == "litellm"


@pytest.mark.parametrize("invalid", [True, "0.25", math.nan, math.inf, "short"],
                         ids=["bool", "string", "nan", "infinity", "dimension"])
def test_jup023_invalid_embeddings_fail_before_persistence(litellm_settings, gateway_transport, invalid):
    vector = [0.25] * 1536
    if invalid == "short":
        vector.pop()
    else:
        vector[0] = invalid
    gateway_transport.responses.append((200, {"data": [{"embedding": vector}]}, {}))
    provider = get_embedding_provider("litellm", 1536, settings=litellm_settings)
    from app.clients.litellm import ProviderError

    store = FakeVectorStore()
    runner = PipelineRunner(FakeAgentRuntime(), TextChunker(32, 8), provider, store)
    with pytest.raises(ProviderError):
        runner.run({"job_id": "job-1", "tenant_id": "tenant-core", "source": "azure",
                    "text_content": "synthetic document", "metadata": {}})
    assert store.saved_payload is None
    assert len(gateway_transport.calls) == 1
