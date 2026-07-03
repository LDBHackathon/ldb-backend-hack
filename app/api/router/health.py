from http import HTTPMethod

from fastapi import APIRouter, status

from app.api.controller.health import health_check
from app.schemas.responses.generic import SuccessResponseSchema

router = APIRouter(tags=["Health"])

router.add_api_route(
    "/health",
    health_check,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[dict[str, str]],
    status_code=status.HTTP_200_OK,
)
