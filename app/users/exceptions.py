from fastapi import status

from app.core.exceptions import AppError


class UserError(AppError):
    pass


class UserAlreadyExistsError(UserError):
    status_code = status.HTTP_409_CONFLICT
    detail = "User already exists"


class UserNotFoundError(UserError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "User not found"
