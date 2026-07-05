import bcrypt


def hash_password(raw_password: str) -> str:
    """Hash a plaintext password."""
    return bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()


def verify_password(raw_password: str, password_hash: str | None) -> bool:
    """Verify a plaintext password against a stored hash."""
    if not password_hash:
        return False
    return bcrypt.checkpw(raw_password.encode(), password_hash.encode())
