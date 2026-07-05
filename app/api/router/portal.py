from http import HTTPMethod

from fastapi import APIRouter, status

from app.api.controller.auth_portal import (
    onboarding_address,
    onboarding_business,
    onboarding_document,
    onboarding_status,
    onboarding_submit,
    onboarding_verification,
    settings_change_password,
    settings_credentials,
    settings_get_profile,
    settings_get_webhook,
    settings_rotate_credentials,
    settings_test_webhook,
    settings_update_profile,
    settings_update_webhook,
)
from app.api.controller.portal import (
    dashboard_summary,
    get_portal_customer,
    get_portal_customer_statement,
    list_portal_customers,
    list_portal_transactions,
    portal_recent_transactions,
    portal_simulate_transfer,
    portal_transactions_summary,
)
from app.schemas.responses.generic import ErrorResponseSchema, SuccessResponseSchema
from app.schemas.responses.onboarding import OnboardingDocumentsListResponseSchema

from . import file_upload

router = APIRouter(prefix="/portal", tags=["Portal"])

router.add_api_route(
    "/dashboard/summary",
    dashboard_summary,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/customers",
    list_portal_customers,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[list],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/customers/{customer_id}",
    get_portal_customer,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema}},
)

router.add_api_route(
    "/customers/{customer_id}/statement",
    get_portal_customer_statement,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/transactions",
    list_portal_transactions,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[list],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/transactions/summary",
    portal_transactions_summary,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/transactions/recent",
    portal_recent_transactions,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[list],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/simulate-transfer",
    portal_simulate_transfer,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/onboarding/business",
    onboarding_business,
    methods=[HTTPMethod.PATCH],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/onboarding/address",
    onboarding_address,
    methods=[HTTPMethod.PATCH],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/onboarding/verification",
    onboarding_verification,
    methods=[HTTPMethod.PATCH],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/onboarding/documents",
    onboarding_document,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[OnboardingDocumentsListResponseSchema],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponseSchema},
    },
)

router.add_api_route(
    "/onboarding/submit",
    onboarding_submit,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/onboarding/status",
    onboarding_status,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/settings/credentials",
    settings_credentials,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/settings/credentials/rotate",
    settings_rotate_credentials,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_201_CREATED,
)

router.add_api_route(
    "/settings/webhook",
    settings_get_webhook,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/settings/webhook",
    settings_update_webhook,
    methods=[HTTPMethod.PUT],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/settings/webhook/test",
    settings_test_webhook,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/settings/profile",
    settings_get_profile,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/settings/profile",
    settings_update_profile,
    methods=[HTTPMethod.PATCH],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/settings/security/password",
    settings_change_password,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.include_router(file_upload.router)
