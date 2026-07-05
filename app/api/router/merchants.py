from http import HTTPMethod

from fastapi import APIRouter, status

from app.api.controller.merchants import get_merchant_profile, register_merchant
from app.schemas.responses.generic import (
    ErrorResponseSchema,
    SuccessResponseSchema,
    ValidationErrorResponseSchema,
)
from app.schemas.responses.merchants import MerchantResponse, RegisterMerchantResponse

router = APIRouter(prefix="/merchants", tags=["Merchants"])

router.add_api_route(
    "/register",
    register_merchant,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[RegisterMerchantResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponseSchema},
    },
)

router.add_api_route(
    "/me",
    get_merchant_profile,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[MerchantResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema},
    },
)
