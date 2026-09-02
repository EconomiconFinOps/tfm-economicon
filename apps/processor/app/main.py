from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.request_context import RequestIdMiddleware
from app.db.database import Database
from app.api.routes.health import router as health_router
from app.clients.rabbitmq_queue import RabbitMQQueue
from app.vector_store.pgvector_store import PgVectorStore


settings = get_settings()
configure_logging()
database = Database(settings.database_url)
queue = RabbitMQQueue(settings.rabbitmq_url, settings.processor_queue_name)
vector_store = PgVectorStore(settings.vector_database_url, settings.embedding_dimension)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.initialize()
    vector_store.initialize()
    app.state.database = database
    app.state.queue = queue
    app.state.vector_store = vector_store
    yield
    queue.close()
    vector_store.close()
    database.dispose()


app = FastAPI(
    title="FinOps Processor",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)

app.include_router(health_router)
