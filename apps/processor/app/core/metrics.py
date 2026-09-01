import time

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

http_requests_total = Counter(
    "processor_http_requests_total",
    "Total HTTP requests handled by the processor",
    ["method", "path", "status_code"],
)

http_request_duration_ms = Histogram(
    "processor_http_request_duration_ms",
    "HTTP request duration in milliseconds",
    ["method", "path"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        route = request.scope.get("route")
        path = route.path if route is not None else request.url.path

        http_requests_total.labels(
            method=request.method,
            path=path,
            status_code=str(response.status_code),
        ).inc()
        http_request_duration_ms.labels(method=request.method, path=path).observe(duration_ms)

        return response


metrics_router = APIRouter()


@metrics_router.get("/metrics")
def get_metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
