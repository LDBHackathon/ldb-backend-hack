from pydantic import BaseModel, Field


class UpdateWebhookSettingsRequestSchema(BaseModel):
    """Update merchant webhook configuration."""

    url: str = Field(..., max_length=500)
    secret: str = Field(..., min_length=16, max_length=255)
    events: list[str] = Field(default_factory=list)
    active: bool = True


class UpdateProfileSettingsRequestSchema(BaseModel):
    """Update merchant profile from settings."""

    name: str | None = Field(None, min_length=2, max_length=200)
    phone: str | None = Field(None, max_length=50)
