from pydantic import BaseModel, EmailStr, Field


class RegisterMerchantRequestSchema(BaseModel):
    """Register a new LDB merchant."""

    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
