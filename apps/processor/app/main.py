from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.database import Database
from app.api.routes.health import router as health_router
from app.clients.rabbitmq_queue import RabbitMQQueue


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
    title="FinOps Processor",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
