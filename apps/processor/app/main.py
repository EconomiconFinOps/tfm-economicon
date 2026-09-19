from contextlib import ExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.metrics import MetricsMiddleware, metrics_router
from app.core.request_context import RequestIdMiddleware, validation_error_handler
from app.core.runtime_secrets import StartupError
from app.db.database import Database
from app.api.routes.health import router as health_router
from app.clients.rabbitmq_queue import RabbitMQQueue
from app.vector_store.pgvector_store import PgVectorStore


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
            vector_store = PgVectorStore(settings.vector_database_url.get_secret_value(), settings.embedding_dimension)
            resources.callback(vector_store.close)
            database.initialize()
            vector_store.initialize()
            app.state.database = database
            app.state.queue = queue
            app.state.vector_store = vector_store
            yield
    except StartupError:
        raise
    except Exception:
        raise StartupError("Service initialization or shutdown failed; check dependency availability.") from None


app = FastAPI(
    title="FinOps Processor",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_middleware(MetricsMiddleware)

app.include_router(metrics_router)
app.include_router(health_router)
