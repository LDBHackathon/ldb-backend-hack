from http import HTTPMethod

from fastapi import APIRouter, status

from app.api.controller.file_upload import (
    delete_file,
    get_file_info,
    upload_multiple_files,
    upload_single_file,
)
from app.schemas.responses.file_upload import (
    FileInformationResponse,
    FilePublicResponse,
    MultipleUploadFileResponse,
    UploadFileResponse,
)
from app.schemas.responses.generic import (
    ErrorResponseSchema,
    SuccessResponseSchema,
    ValidationErrorResponseSchema,
)

router = APIRouter(prefix="/files", tags=["File Upload"])

router.add_api_route(
    "/upload",
    upload_single_file,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[UploadFileResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponseSchema},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponseSchema},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponseSchema},
    },
)

router.add_api_route(
    "/upload/multiple",
    upload_multiple_files,
    methods=[HTTPMethod.POST],
    response_model=SuccessResponseSchema[MultipleUploadFileResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponseSchema},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponseSchema},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponseSchema},
    },
)

router.add_api_route(
    "/{public_id:path}",
    delete_file,
    methods=[HTTPMethod.DELETE],
    response_model=SuccessResponseSchema[FilePublicResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponseSchema},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponseSchema},
    },
)

router.add_api_route(
    "/{public_id:path}/info",
    get_file_info,
    methods=[HTTPMethod.GET],
    response_model=SuccessResponseSchema[FileInformationResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponseSchema},
    },
)
