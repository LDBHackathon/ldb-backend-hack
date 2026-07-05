from pydantic import BaseModel, Field


class OnboardingBusinessRequestSchema(BaseModel):
    """KYB step 2 — business details."""

    business_name: str = Field(min_length=2, max_length=200)
    trading_name: str | None = Field(None, max_length=200)
    business_type: str | None = Field(None, max_length=100)
    tax_id: str | None = Field(None, max_length=50)
    registration_number: str | None = Field(None, max_length=50)
    industry: str | None = Field(None, max_length=100)


class OnboardingAddressRequestSchema(BaseModel):
    """KYB step 3 — address and contact."""

    address_line: str = Field(min_length=5, max_length=300)
    city: str = Field(min_length=2, max_length=100)
    state: str | None = Field(None, max_length=100)
    country: str = Field(default="Nigeria", max_length=100)
    business_phone: str | None = Field(None, max_length=50)
    website: str | None = Field(None, max_length=300)


class OnboardingVerificationRequestSchema(BaseModel):
    """KYB step 4 — director and documents."""

    director_name: str = Field(min_length=2, max_length=200)
    bvn_id: str | None = Field(None, min_length=11, max_length=11)
    cac_document_url: str | None = Field(None, max_length=500)
    address_proof_url: str | None = Field(None, max_length=500)
    notes: str | None = Field(None, max_length=1000)
    consent: bool = Field(default=False)
