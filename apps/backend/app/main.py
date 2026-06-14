from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.billing import router as billing_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.tenants import router as tenants_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.database import Database
from app.services.rabbitmq_queue import RabbitMQQueue


settings = get_settings()
configure_logging()
database = Database(settings.database_url)
queue = RabbitMQQueue(settings.rabbitmq_url, settings.processor_queue_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.initialize()
    app.state.database = database
    app.state.queue = queue
    yield
    queue.close()
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
