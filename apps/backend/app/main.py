from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.assistant import router as assistant_router
from app.api.routes.auth import router as auth_router
from app.api.routes.billing import router as billing_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.tenants import router as tenants_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.database import Database
from app.services.assistant import AssistantService
from app.services.embedding_provider import MockEmbeddingProvider
from app.services.rabbitmq_queue import RabbitMQQueue
from app.services.vector_store import PgVectorQueryStore


settings = get_settings()
configure_logging()
database = Database(settings.database_url)
queue = RabbitMQQueue(settings.rabbitmq_url, settings.processor_queue_name)
vector_store = PgVectorQueryStore(settings.vector_database_url)
assistant_service = AssistantService()
embedding_provider = MockEmbeddingProvider(settings.embedding_dimension)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.initialize()
    app.state.database = database
    app.state.queue = queue
    app.state.vector_store = vector_store
    app.state.assistant_service = assistant_service
    app.state.embedding_provider = embedding_provider
    yield
    queue.close()
    vector_store.close()
    database.dispose()


app = FastAPI(
    title="FinOps Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(tenants_router)
app.include_router(billing_router)
app.include_router(jobs_router)
app.include_router(assistant_router)
