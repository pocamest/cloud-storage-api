from enum import StrEnum

from fastapi import status


class ErrorCode(StrEnum):
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    BAD_REQUEST = "BAD_REQUEST"

    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_NOT_FOUND = "USER_NOT_FOUND"

    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_INVALID_TYPE = "TOKEN_INVALID_TYPE"

    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FOLDER_NOT_FOUND = "FOLDER_NOT_FOUND"
    NAME_ALREADY_TAKEN = "NAME_ALREADY_TAKEN"
    FOLDER_TARGET_IS_SELF = "FOLDER_TARGET_IS_SELF"
    FOLDER_TARGET_IS_SUBFOLDER = "FOLDER_TARGET_IS_SUBFOLDER"


class AppError(Exception):
    """
    Базовый класс для всех ожидаемых ошибок.

    Все непредвиденные баги возвращаются клиенту в виде 500 ошибки.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Application error"
    error_code = ErrorCode.BAD_REQUEST

    def __init__(self, detail: str | None = None, error_code: ErrorCode | None = None):
        if detail:
            self.detail = detail
        if error_code:
            self.error_code = error_code
        super().__init__(self.detail)
