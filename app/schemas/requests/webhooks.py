from pydantic import BaseModel, Field


class RegisterWebhookRequestSchema(BaseModel):
    """Register a merchant webhook URL."""

    url: str = Field(..., max_length=500)
    secret: str = Field(..., min_length=16, max_length=255)
    events: list[str] = Field(default_factory=lambda: ["customer.payment_received"])
