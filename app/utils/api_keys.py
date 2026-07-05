import hashlib
import secrets

from app.settings import settings


def generate_api_key() -> str:
    """Generate a new merchant API key."""
    env_label = "live" if settings.PROD_ENV else "test"
    return f"ldb_{env_label}_{secrets.token_hex(32)}"


def api_key_prefix(raw_key: str) -> str:
    """Return a stable lookup prefix for an API key."""
    return raw_key[:16]


def hash_api_key(raw_key: str) -> str:
    """Hash an API key with the application secret pepper."""
    payload = f"{settings.SECRET_KEY}:{raw_key}".encode()
    return hashlib.sha256(payload).hexdigest()
