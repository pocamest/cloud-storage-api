import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)


def internal_server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Error at {request.url}", exc_info=exc)
    return JSONResponse(content={"detail": "Internal server error"}, status_code=500)


def register_exceptions_handler(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, internal_server_error_handler)
