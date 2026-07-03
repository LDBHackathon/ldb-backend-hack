from http import HTTPMethod
from typing import Any

from fastapi import APIRouter, status

from app.api.controller.hooks import register_webhook
from app.schemas.responses.generic import (
    ErrorResponseSchema,
    SuccessResponseSchema,
    ValidationErrorResponseSchema,
)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

router.add_api_route(
    "/register",
    register_webhook,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponseSchema},
    },
)
