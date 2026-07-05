from pydantic import BaseModel, EmailStr, Field


class RegisterAuthRequestSchema(BaseModel):
    """Register merchant account with dashboard login."""

    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginAuthRequestSchema(BaseModel):
    """Dashboard sign-in."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequestSchema(BaseModel):
    """Change dashboard password."""

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
