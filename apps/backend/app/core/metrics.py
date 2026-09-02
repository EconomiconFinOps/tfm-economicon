from time import perf_counter

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

http_requests_total = Counter(
    "backend_http_requests_total",
    "Total HTTP requests handled by the backend",
    ["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "backend_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

ingest_jobs_total = Counter(
    "backend_ingest_jobs_total",
    "Total ingest jobs created",
)

assistant_queries_total = Counter(
    "backend_assistant_queries_total",
    "Total assistant queries answered",
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            self._record(request, status_code=500, start=start)
            raise

        self._record(request, status_code=response.status_code, start=start)

        return response

    @staticmethod
    def _record(request, status_code: int, start: float) -> None:
        duration_seconds = perf_counter() - start
        route = request.scope.get("route")
        path = route.path if route is not None else "__unmatched__"

        http_requests_total.labels(
            method=request.method,
            path=path,
            status_code=str(status_code),
        ).inc()
        http_request_duration_seconds.labels(method=request.method, path=path).observe(
            duration_seconds
        )


metrics_router = APIRouter()


@metrics_router.get("/metrics")
def get_metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
