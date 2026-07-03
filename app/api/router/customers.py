from http import HTTPMethod

from fastapi import APIRouter, status

from app.api.controller.customers import create_customer, get_customer, update_customer
from app.schemas.responses.customers import CustomerResponse
from app.schemas.responses.generic import (
    ErrorResponseSchema,
    SuccessResponseSchema,
    ValidationErrorResponseSchema,
)

router = APIRouter(prefix="/customers", tags=["Customers"])

router.add_api_route(
    "",
    create_customer,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[CustomerResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponseSchema},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponseSchema},
    },
)

router.add_api_route(
    "/{customer_id}",
    get_customer,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[CustomerResponse],
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema}},
)

router.add_api_route(
    "/{customer_id}",
    update_customer,
    methods=[HTTPMethod.PATCH],
    response_model=SuccessResponseSchema[CustomerResponse],
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema}},
)
