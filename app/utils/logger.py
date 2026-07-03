"""Logger utility for the application."""

import logging
from pathlib import Path

import orjson
import structlog

from app.settings import settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

_shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.StackInfoRenderer(),
    structlog.dev.set_exc_info,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
]

structlog.configure(
    processors=(
        [
            *_shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.EventRenamer("event_message"),
            structlog.processors.JSONRenderer(serializer=orjson.dumps),
        ]
        if settings.FILE_LOGGING
        else [*_shared_processors, structlog.dev.ConsoleRenderer()]
    ),
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.INFO if settings.FILE_LOGGING else logging.DEBUG
    ),
    logger_factory=(
        structlog.BytesLoggerFactory((LOGS_DIR / "app.log").open("ab"))
        if settings.FILE_LOGGING
        else structlog.WriteLoggerFactory()
    ),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger().bind(service="LDB DVA API")


def bind_request_context(correlation_id: str, ip_address: str) -> None:
    """Bind request-scoped fields to structlog contextvars."""
    structlog.contextvars.bind_contextvars(
        correlation_id=correlation_id, ip_address=ip_address
    )


def clear_request_context() -> None:
    """Clear request-scoped contextvars after request completion."""
    structlog.contextvars.clear_contextvars()
