"""Tortoise ORM configuration."""

from functools import partial
from urllib.parse import parse_qs, urlparse, urlunparse

from tortoise.contrib.fastapi import RegisterTortoise

from app.settings import settings


def _build_db_url() -> str:
    """Normalize DB URL for tortoise-orm/asyncpg compatibility."""
    url = str(settings.DB_URL).replace("postgresql://", "postgres://")
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    ssl = query.get("sslmode", ["disable"])[0] in (
        "require",
        "verify-ca",
        "verify-full",
    )
    clean_url = urlunparse(parsed._replace(query=""))
    if ssl:
        clean_url += "?ssl=true"
    return clean_url


TORTOISE_CONFIG: dict[str, str | dict[str, str | dict[str, str | list[str]]]] = {
    "connections": {"default": _build_db_url()},
    "apps": {
        "main": {
            "models": ["app.models"],
            "default_connection": "default",
            "migrations": "app.migrations",
        }
    },
}

register_orm = partial(
    RegisterTortoise,
    config=TORTOISE_CONFIG,
    generate_schemas=True,
)
