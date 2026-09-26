import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

HTTP_REQUESTS = Counter(
    "orderpilot_http_requests_total",
    "HTTP requests handled by OrderPilot",
    ["method", "path", "status"],
)
HTTP_LATENCY = Histogram(
    "orderpilot_http_request_duration_seconds",
    "OrderPilot HTTP request latency",
    ["method", "path"],
)
IMPORTS = Counter(
    "orderpilot_imports_total",
    "Order imports by source and result",
    ["source", "result"],
)
AI_REQUESTS = Counter(
    "orderpilot_ai_requests_total",
    "AI extraction attempts and outcomes",
    ["result"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = time.perf_counter()
        response_status = 500
        try:
            response = await call_next(request)
            response_status = response.status_code
            return response
        finally:
            route = request.scope.get("route")
            path = getattr(route, "path", request.url.path)
            HTTP_REQUESTS.labels(request.method, path, str(response_status)).inc()
            HTTP_LATENCY.labels(request.method, path).observe(time.perf_counter() - started)


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
