from http import HTTPMethod
from typing import Any

from fastapi import APIRouter, status

from app.api.controller.hooks import nomba_webhook, simulate_funding
from app.schemas.responses.generic import (
    ErrorResponseSchema,
    SuccessResponseSchema,
    ValidationErrorResponseSchema,
)

router = APIRouter(prefix="/hooks", tags=["Hooks"])

router.add_api_route(
    "/nomba",
    nomba_webhook,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponseSchema},
    },
)

router.add_api_route(
    "/simulate",
    simulate_funding,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponseSchema},
    },
)
