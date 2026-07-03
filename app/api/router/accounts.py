from http import HTTPMethod

from fastapi import APIRouter, status

from app.api.controller.accounts import (
    create_dedicated_account,
    get_account,
    get_statement,
    list_transactions,
)
from app.schemas.responses.accounts import AccountResponse, StatementResponse
from app.schemas.responses.generic import (
    ErrorResponseSchema,
    PaginatedResponseSchema,
    SuccessResponseSchema,
    ValidationErrorResponseSchema,
)
from app.schemas.responses.transactions import TransactionResponse

router = APIRouter(prefix="/accounts", tags=["Accounts"])

router.add_api_route(
    "/dedicated",
    create_dedicated_account,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[AccountResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema},
        status.HTTP_409_CONFLICT: {"model": ErrorResponseSchema},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponseSchema},
    },
)

router.add_api_route(
    "/{account_id}",
    get_account,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[AccountResponse],
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema}},
)

router.add_api_route(
    "/{account_id}/transactions",
    list_transactions,
    methods=[HTTPMethod.GET],
    response_model=PaginatedResponseSchema[TransactionResponse],
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema}},
)

router.add_api_route(
    "/{account_id}/statement",
    get_statement,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[StatementResponse],
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema}},
)
