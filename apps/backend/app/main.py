import asyncio
import os
from contextlib import ExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp

from app.api.routes.assistant import router as assistant_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
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
from app.core.embedding_startup import log_embedding_configuration
from app.services.embedding_provider import LiteLLMEmbeddingProvider, MockEmbeddingProvider
from app.services import reference_date
from app.services.rabbitmq_queue import RabbitMQQueue
from app.services.vector_store import PgVectorQueryStore


configure_logging()


async def initialize_chat_resources(application):
    application.state.summary_resources=None
    application.state.chat_enabled=os.getenv('CHAT_ENABLED','false').lower()=='true'
    if not application.state.chat_enabled:
        return
    configured=os.getenv('CHAT_MAX_ACTIVE','8').strip()
    if configured not in {'5','6','7','8'}:
        raise StartupError('Chat capacity configuration is invalid.')
    application.state.chat_max_active=int(configured)
    from app.core.chat_resources import load_resources
    from app.services.chat_context import ChatContext
    resources=getattr(application.state,'chat_resources',None)
    if resources is None:
        try:
            resources=await asyncio.to_thread(load_resources,os.getenv('CHAT_RESOURCE_DIRECTORY'),os.getenv('CHAT_TOKENIZER_FILE'))
        except Exception:
            application.state.chat_resources=None
            application.state.chat_context_builder=None
            return
    application.state.chat_resources=resources
    application.state.chat_context_builder=ChatContext(application,resources)
    try:
        from app.core.summary_resources import load_resources as load_summary_resources
        application.state.summary_resources=await asyncio.to_thread(load_summary_resources,os.getenv('SUMMARY_RESOURCE_DIRECTORY'),os.getenv('CHAT_TOKENIZER_FILE'))
    except Exception:
        application.state.summary_resources=None
    from app.services.chat_operations import service
    service(application,active=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        settings = get_settings()
        configure_logging()
        reference_date.configure(settings.cost_reference_date)
        with ExitStack() as resources:
            database = Database(settings.database_url.get_secret_value())
            resources.callback(database.dispose)
            queue = RabbitMQQueue(settings.rabbitmq_url.get_secret_value(), settings.processor_queue_name)
            resources.callback(queue.close)
            vector_store = PgVectorQueryStore(settings.vector_database_url.get_secret_value())
            resources.callback(vector_store.close)
            database.initialize()
            queue.start()
            app.state.database = database
            app.state.queue = queue
            app.state.vector_store = vector_store
            app.state.assistant_service = AssistantService()
            embedding_provider = (
                LiteLLMEmbeddingProvider(settings) if settings.embedding_provider == "litellm"
                else MockEmbeddingProvider(settings.embedding_dimension)
            )
            vector_store.verify_dimension(embedding_provider.dimension)
            log_embedding_configuration(settings)
            app.state.embedding_provider = embedding_provider
            await initialize_chat_resources(app)
            try:
                yield
            finally:
                chat = getattr(app.state, "chat_service", None)
                if chat is not None:
                    await chat.close()
    except StartupError:
        raise
    except Exception:
        raise StartupError("Service initialization or shutdown failed; check dependency availability.") from None


class RuntimeCORSMiddleware(CORSMiddleware):
    def __init__(self, app: ASGIApp):
        # Settings are resolved when ASGI builds the stack, never during import.
        super().__init__(
            app,
            allow_origins=get_settings().cors_allowed_origins,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Tenant-Id"],
            allow_credentials=False,
            expose_headers=[],
            max_age=600,
        )


app = FastAPI(
    title="FinOps Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RuntimeCORSMiddleware)

app.include_router(metrics_router)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(tenants_router)
app.include_router(billing_router)
app.include_router(jobs_router)
app.include_router(assistant_router)
app.include_router(chat_router)
