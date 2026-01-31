import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError, ErrorCode
from app.core.schemas import ErrorResponse

logger = logging.getLogger(__name__)


def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    error_response = ErrorResponse.model_validate(exc)
    return JSONResponse(
        content=error_response.model_dump(),
        status_code=exc.status_code,
    )


def internal_server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Error at {request.url}", exc_info=exc)
    error_response = ErrorResponse(
        detail="Internal server error", code=ErrorCode.INTERNAL_SERVER_ERROR
    )
    return JSONResponse(
        content=error_response.model_dump(),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def register_exceptions_handler(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, internal_server_error_handler)
