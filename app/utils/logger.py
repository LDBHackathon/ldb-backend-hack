"""Minimal logging shim; info/debug are silent so Docker shows uvicorn access logs only."""

import logging
from typing import Any


def _format_message(message: str, **kwargs: Any) -> str:
    if not kwargs:
        return message
    extras = " ".join(f"{key}={value}" for key, value in kwargs.items())
    return f"{message} {extras}"


class _SilentInfoLogger:
    """Accept structlog-style kwargs but only emit warning-level and above."""

    def __init__(self) -> None:
        self._log = logging.getLogger("ldb")

    def debug(self, message: str, **kwargs: Any) -> None:
        pass

    def info(self, message: str, **kwargs: Any) -> None:
        pass

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log.warning(_format_message(message, **kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        self._log.error(_format_message(message, **kwargs))

    def exception(self, message: str, **kwargs: Any) -> None:
        self._log.exception(_format_message(message, **kwargs))


logger = _SilentInfoLogger()
