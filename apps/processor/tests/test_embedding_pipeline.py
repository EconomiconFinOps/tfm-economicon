from app.embeddings.chunker import TextChunker
from app.embeddings.providers import MockEmbeddingProvider
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
