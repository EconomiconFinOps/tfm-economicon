from app.api.routes.assistant import send_message
from app.api.routes.jobs import create_ingest_job
from app.core import metrics
from app.schemas.assistant import MessageCreateRequest
from app.schemas.jobs import IngestJobRequest
from app.services.rabbitmq_queue import PublishResult
from test_chat_operations_jup035 import api, body, headers, path, run


class _FakeQueue:
    queue_name = "processor:jobs"

    def __init__(self):
        self.reservation = object()

    def reserve(self):
        return self.reservation

    def publish(self, job, *, reservation):
        assert reservation is self.reservation
        return PublishResult("confirmed", "confirmed")

    def cancel(self, reservation):
        assert reservation is self.reservation


class _FakeDatabase:
    def create_job(self, payload, created_by):
        self.job = {"id": "job-1", "status": "queued", "created_by": created_by, **payload}
        return self.job

    def finalize_job_publication(self, job_id, *, tenant_id, created_by, outcome, code):
        assert (job_id, tenant_id, created_by) == (self.job["id"], self.job["tenant_id"], self.job["created_by"])
        assert (outcome, code) == ("confirmed", "confirmed")

    def fetch_conversation(self, conversation_id, tenant_id, user_id):
        return {
            "id": conversation_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "title": "test",
            "created_at": "2026-09-01T00:00:00Z",
            "updated_at": "2026-09-01T00:00:00Z",
        }

    def assert_conversation_idle(self, **scope):
        return None

    def prepare_message(self, **kwargs):
        return {"id": "message-" + kwargs["role"], "created_at": "2026-09-01T00:00:00Z", "metadata": {}, **kwargs}

    def append_pair(self, *, question, assistant):
        assert question["role"] == "user" and assistant["role"] == "assistant"
        return question, assistant

    def append_message(self, **kwargs):
        return {
            "id": "message-1",
            "created_at": "2026-09-01T00:00:00Z",
            "metadata": {},
            **kwargs,
        }


class _FakeVectorStore:
    def search_chunks(self, tenant_id, query_embedding, top_k, max_distance, provider=None):
        return []


class _FakeEmbeddingProvider:
    name = "mock"
    dimension = 1

    def embed(self, content):
        return [1.0]


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


def test_new_generation_counts_once_and_replay_does_not_count_again(api):
    before = metrics.assistant_queries_total._value.get()
    async def scenario(client):
        payload = body()
        first = await client.post(path(), json=payload, headers=headers())
        assert first.status_code == 200 and "event: final" in first.text
        repeated = await client.post(path(), json=payload, headers=headers())
        assert repeated.status_code == 200 and repeated.json()["outcome"] == "existing"
    run(scenario, api)
    assert metrics.assistant_queries_total._value.get() == before + 1
