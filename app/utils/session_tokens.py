from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt

from app.settings import settings

SESSION_ALGORITHM = "HS256"


def create_session_token(merchant_id: UUID) -> str:
    """Create a signed JWT for dashboard session auth."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(merchant_id),
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(hours=settings.SESSION_JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=SESSION_ALGORITHM)


def decode_session_token(token: str) -> dict[str, Any]:
    """Decode and validate a session JWT."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[SESSION_ALGORITHM])
