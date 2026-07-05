from pathlib import Path

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class EnvSettings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=BASE_DIR.parent / ".env", extra="ignore")

    PROD_ENV: bool = False
    FILE_LOGGING: bool = False

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    SECRET_KEY: str = "dev-secret-key"
    DB_URL: PostgresDsn | str = "postgresql://ldb:ldb@localhost:5432/ldb_dva"
    REDIS_URL: str = "redis://localhost:6379/0"

    LDB_API_KEY: str = "dev-api-key"
    DEFAULT_MERCHANT_ID: str = "00000000-0000-0000-0000-000000000001"

    NOMBA_CLIENT_ID: str = ""
    NOMBA_CLIENT_SECRET: str = ""  # Nomba "private key" from dashboard
    NOMBA_ACCOUNT_ID: str = ""  # Parent account ID (accountId header)
    NOMBA_SUB_ACCOUNT_ID: str = ""  # Your sub-account ID for scoped calls
    NOMBA_BASE_URL: str = "https://sandbox.nomba.com"
    NOMBA_WEBHOOK_SECRET: str = ""

    SESSION_COOKIE_NAME: str = "ldb_session"
    SESSION_JWT_EXPIRY_HOURS: int = Field(default=24, ge=1, le=168)

    NIGHTLY_RECONCILIATION_HOUR: int = Field(default=2, ge=0, le=23)

    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""


settings = EnvSettings()
