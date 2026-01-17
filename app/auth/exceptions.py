from fastapi import status

from app.core.exceptions import AppError


class AuthError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED


class InvalidCredentialsError(AuthError):
    detail = "Invalid credentials"


class TokenExpiredError(AuthError):
    detail = "Token expired"


class TokenInvalidError(AuthError):
    detail = "Invalid Token"
