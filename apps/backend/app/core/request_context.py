import time
import uuid

import structlog
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger("access")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error("http_request_failed", error_code="internal_error", exception_type=type(exc).__name__)
            response = JSONResponse({"detail": "Internal server error"}, status_code=500)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "http_request",
            method=request.method,
            path=getattr(request.scope.get("route"), "path", "__unmatched__"),
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response


async def validation_error_handler(request, exc: RequestValidationError):
    # Mapping keys in validation locations can also contain user input.
    return JSONResponse(
        {"detail": [{"type": "validation_error", "msg": "Invalid request value"} for _ in exc.errors()]},
        status_code=422,
    )
