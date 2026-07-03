import re

from fastapi import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.utils.metrics import http_request_duration, http_requests_total


class MetricsMiddleware:
    """Prometheus metrics middleware."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            request = Request(scope)

            with http_request_duration.labels(
                method=request.method,
                path=self._normalize_path(request.url.path),
            ).time():

                async def send_wrapper(message: Message) -> None:
                    if message["type"] == "http.response.start":
                        http_requests_total.labels(
                            method=request.method,
                            path=self._normalize_path(request.url.path),
                            status_code=int(message.get("status", 0)),
                        ).inc()
                    await send(message)

                await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

    def _normalize_path(self, path: str) -> str:
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            ":id",
            path,
        )
        return re.sub(r"/\d+", "/:num", path)
