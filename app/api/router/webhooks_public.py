from http import HTTPMethod
from typing import Any

from fastapi import APIRouter, status

from app.api.controller.portal import portal_simulate_transfer
from app.schemas.responses.generic import SuccessResponseSchema

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

router.add_api_route(
    "/dva-funding",
    portal_simulate_transfer,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
