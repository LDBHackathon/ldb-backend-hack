from http import HTTPMethod

from fastapi import APIRouter, status

from app.api.controller.v1 import (
    v1_create_customer,
    v1_get_customer,
    v1_get_customer_statement,
    v1_register_webhook,
    v1_update_customer,
)
from app.schemas.responses.customers import CustomerResponse
from app.schemas.responses.generic import ErrorResponseSchema, SuccessResponseSchema

router = APIRouter(prefix="/v1", tags=["Developer v1"])

router.add_api_route(
    "/customers",
    v1_create_customer,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[CustomerResponse],
    status_code=status.HTTP_201_CREATED,
)

router.add_api_route(
    "/customers/{customer_id}",
    v1_get_customer,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[CustomerResponse],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/customers/{customer_id}",
    v1_update_customer,
    methods=[HTTPMethod.PATCH],
    response_model=SuccessResponseSchema[CustomerResponse],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/customers/{customer_id}/statement",
    v1_get_customer_statement,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/webhooks",
    v1_register_webhook,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema}},
)
