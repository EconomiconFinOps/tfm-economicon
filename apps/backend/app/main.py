from contextlib import ExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.routes.assistant import router as assistant_router
from app.api.routes.auth import router as auth_router
from app.api.routes.billing import router as billing_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.tenants import router as tenants_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.metrics import MetricsMiddleware, metrics_router
from app.core.request_context import RequestIdMiddleware, validation_error_handler
from app.core.runtime_secrets import StartupError
from app.db.database import Database
from app.services.assistant import AssistantService
from app.services.embedding_provider import MockEmbeddingProvider
from app.services.rabbitmq_queue import RabbitMQQueue
from app.services.vector_store import PgVectorQueryStore


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        settings = get_settings()
        configure_logging()
        with ExitStack() as resources:
            database = Database(settings.database_url.get_secret_value())
            resources.callback(database.dispose)
            queue = RabbitMQQueue(settings.rabbitmq_url.get_secret_value(), settings.processor_queue_name)
            resources.callback(queue.close)
            vector_store = PgVectorQueryStore(settings.vector_database_url.get_secret_value())
            resources.callback(vector_store.close)
            database.initialize()
            app.state.database = database
            app.state.queue = queue
            app.state.vector_store = vector_store
            app.state.assistant_service = AssistantService()
            app.state.embedding_provider = MockEmbeddingProvider(settings.embedding_dimension)
            yield
    except StartupError:
        raise
    except Exception:
        raise StartupError("Service initialization or shutdown failed; check dependency availability.") from None


app = FastAPI(
    title="FinOps Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_middleware(MetricsMiddleware)

app.include_router(metrics_router)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(tenants_router)
app.include_router(billing_router)
app.include_router(jobs_router)
app.include_router(assistant_router)
