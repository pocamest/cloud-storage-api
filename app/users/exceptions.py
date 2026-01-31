from fastapi import status

from app.core.exceptions import AppError, ErrorCode


class UserError(AppError):
    pass


class UserAlreadyExistsError(UserError):
    status_code = status.HTTP_409_CONFLICT
    detail = "User already exists"
    error_code = ErrorCode.USER_ALREADY_EXISTS


class UserNotFoundError(UserError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "User not found"
    error_code = ErrorCode.USER_NOT_FOUND
