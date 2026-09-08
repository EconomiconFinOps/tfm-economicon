import time

import structlog

from app.agents.service import AgentRuntime
from app.clients.rabbitmq_queue import QueueMessage, RabbitMQQueue
from app.core.config import Settings
from app.db.database import Database
from app.embeddings.chunker import TextChunker
from app.embeddings.providers import get_embedding_provider
from app.graphs.pipeline import PipelineRunner
from app.repositories.jobs import JobRepository
from app.tasks.ingest import IngestTask
from app.vector_store.pgvector_store import PgVectorStore


logger = structlog.get_logger(__name__)


class ProcessorWorker:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.database = Database(settings.database_url)
        self.queue = RabbitMQQueue(settings.rabbitmq_url, settings.processor_queue_name)
        self.vector_store = PgVectorStore(settings.vector_database_url, settings.embedding_dimension)
        self.repository = JobRepository(self.database)
        self.pipeline = PipelineRunner(
            AgentRuntime(settings),
            TextChunker(settings.embedding_chunk_size, settings.embedding_chunk_overlap),
            get_embedding_provider(settings.embedding_provider, settings.embedding_dimension),
            self.vector_store,
        )
        self.task = IngestTask(self.repository, self.pipeline)

    def run_forever(self) -> None:
        self.database.initialize()
        self.vector_store.initialize()
        logger.info("Processor worker started for queue %s", self.settings.processor_queue_name)

        while True:
            try:
                message = self.queue.blocking_pop(timeout=5)
                if message is None:
                    time.sleep(1)
                    continue
                self._process_message(message)
            except Exception as exc:
                logger.exception("Worker loop failed: %s", exc)
                time.sleep(2)

    def _process_message(self, message: QueueMessage) -> None:
        job = message.payload
        logger.info("Processing job %s", job["id"])

        try:
            self.task.execute(job)
            self.queue.ack(message.delivery_tag)
        except Exception:
            self.queue.nack(message.delivery_tag, requeue=True)
            raise
