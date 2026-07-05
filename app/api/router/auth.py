from http import HTTPMethod

from fastapi import APIRouter, status

from app.api.controller.auth_portal import auth_me, login_auth, logout_auth, register_auth
from app.schemas.responses.generic import ErrorResponseSchema, SuccessResponseSchema

router = APIRouter(prefix="/auth", tags=["Auth"])

router.add_api_route(
    "/register",
    register_auth,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorResponseSchema}},
)

router.add_api_route(
    "/login",
    login_auth,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema}},
)

router.add_api_route(
    "/logout",
    logout_auth,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/me",
    auth_me,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema}},
)
