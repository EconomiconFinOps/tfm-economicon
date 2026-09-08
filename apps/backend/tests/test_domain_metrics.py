from app.api.routes.assistant import send_message
from app.api.routes.jobs import create_ingest_job
from app.core import metrics
from app.schemas.assistant import MessageCreateRequest
from app.schemas.jobs import IngestJobRequest


class _FakeQueue:
    queue_name = "processor:jobs"

    def publish(self, job):
        return True


class _FakeDatabase:
    def create_job(self, payload, created_by):
        return {"id": "job-1", "status": "queued", **payload}

    def fetch_conversation(self, conversation_id, tenant_id, user_id):
        return {
            "id": conversation_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "title": "test",
            "created_at": "2026-09-01T00:00:00Z",
            "updated_at": "2026-09-01T00:00:00Z",
        }

    def append_message(self, **kwargs):
        return {
            "id": "message-1",
            "created_at": "2026-09-01T00:00:00Z",
            "metadata": {},
            **kwargs,
        }


class _FakeVectorStore:
    def search_chunks(self, tenant_id, query_embedding):
        return []


class _FakeEmbeddingProvider:
    def embed(self, content):
        return [0.0]


class _FakeAssistantService:
    def answer(self, content, retrieved_chunks):
        return {"content": "answer", "citations": []}


def test_create_ingest_job_increments_ingest_counter():
    before = metrics.ingest_jobs_total._value.get()

    create_ingest_job(
        payload=IngestJobRequest(
            tenant_id="tenant-core",
            source="aws-cur",
            text_content="report",
        ),
        current_user={"id": "user-1"},
        tenant_id="tenant-core",
        database=_FakeDatabase(),
        queue=_FakeQueue(),
    )

    assert metrics.ingest_jobs_total._value.get() == before + 1


def test_send_message_increments_assistant_queries_counter():
    before = metrics.assistant_queries_total._value.get()

    send_message(
        conversation_id="conversation-1",
        payload=MessageCreateRequest(content="How are my costs?"),
        current_user={"id": "user-1"},
        tenant_id="tenant-core",
        database=_FakeDatabase(),
        vector_store=_FakeVectorStore(),
        embedding_provider=_FakeEmbeddingProvider(),
        assistant_service=_FakeAssistantService(),
    )

    assert metrics.assistant_queries_total._value.get() == before + 1
