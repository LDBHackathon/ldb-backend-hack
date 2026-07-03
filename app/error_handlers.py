from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.main import application
from app.utils.exceptions import ErrorResponse, RateLimitErrorResponse
from app.utils.logger import logger


@application.exception_handler(ErrorResponse)
async def api_error_response_handler(
    _request: Request, exc: ErrorResponse
) -> JSONResponse:
    logger.warning("Handled API error response", error_message=exc.message)
    return JSONResponse(
        {
            "status": "failure",
            "status_code": exc.status,
            "message": exc.message,
            "errors": exc.errors,
        },
        status_code=exc.status,
    )


@application.exception_handler(HTTPException)
async def http_error_response_handler(
    _request: Request, exc: HTTPException
) -> JSONResponse:
    logger.warning(
        "Handled HTTP exception", status_code=exc.status_code, detail=exc.detail
    )
    return JSONResponse(
        {
            "status": "failure",
            "status_code": exc.status_code,
            "message": exc.detail,
            "errors": None,
        },
        status_code=exc.status_code,
    )


@application.exception_handler(RequestValidationError)
async def validation_error_response_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        f"{err['loc'][-1]} {err['msg']}"
        for err in exc.errors()
    ]
    logger.warning("Handled validation error", errors_count=len(errors))
    return JSONResponse(
        jsonable_encoder(
            {
                "status": "failure",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Validation Errors",
                "errors": errors,
            }
        ),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@application.exception_handler(RateLimitErrorResponse)
async def rate_limit_error_response_handler(
    _request: Request, exc: RateLimitErrorResponse
) -> JSONResponse:
    logger.warning("Rate limit exceeded")
    return JSONResponse(
        {
            "status": "failure",
            "status_code": exc.status,
            "message": exc.message,
            "errors": exc.errors,
        },
        status_code=exc.status,
    )


@application.exception_handler(Exception)
async def internal_server_error_response_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled exception occurred", error_message=str(exc))
    return JSONResponse(
        {
            "status": "failure",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Something went wrong on our end. Please try again later",
            "errors": None,
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
