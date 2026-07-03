from uuid import uuid4
from datetime import UTC, datetime

from fastapi import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.datastructures import MutableHeaders

from app.utils.logger import bind_request_context, clear_request_context, logger


class RequestLoggerMiddleware:
    """Log incoming HTTP requests with correlation IDs."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        correlation_id = request.cookies.get("_CCRLID", str(uuid4()))
        ip_address = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if "X-Forwarded-For" in request.headers
            else (request.client.host if request.client else "unknown")
        )

        bind_request_context(correlation_id, ip_address)
        start_time = datetime.now(UTC)

        logger.info(
            "Request received",
            method=request.method,
            path=request.url.path,
        )

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                correlation_cookie = (
                    f"_CCRLID={correlation_id}; Max-Age=86400; Path=/; HttpOnly"
                )
                headers.append("Set-Cookie", correlation_cookie)

                duration = (datetime.now(UTC) - start_time).total_seconds()
                status_code = int(message["status"])
                log_data = dict(
                    correlation_id=correlation_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=status_code,
                    duration_secs=duration,
                )
                if status_code >= 500:
                    logger.error("Request failed", **log_data)
                elif status_code >= 400:
                    logger.warning("Request client error", **log_data)
                else:
                    logger.info("Request completed", **log_data)

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            clear_request_context()
