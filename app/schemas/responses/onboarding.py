from pydantic import BaseModel, Field


class OnboardingDocumentResponseSchema(BaseModel):
    """Uploaded KYB document metadata."""

    document_type: str
    file_url: str
    public_id: str
    original_filename: str | None = None
    file_type: str | None = None
    file_size: int | None = None


class OnboardingDocumentsListResponseSchema(BaseModel):
    """List of uploaded KYB documents."""

    document: OnboardingDocumentResponseSchema
    documents: list[OnboardingDocumentResponseSchema]
