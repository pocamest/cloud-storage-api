from enum import StrEnum

from fastapi import status


class ErrorCode(StrEnum):
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"

    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_NOT_FOUND = "USER_NOT_FOUND"

    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_INVALID_TYPE = "TOKEN_INVALID_TYPE"


class AppError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Internal server error"
    error_code = ErrorCode.INTERNAL_SERVER_ERROR

    def __init__(self, detail: str | None = None, error_code: ErrorCode | None = None):
        if detail:
            self.detail = detail
        if error_code:
            self.error_code = error_code
        super().__init__(self.detail)
