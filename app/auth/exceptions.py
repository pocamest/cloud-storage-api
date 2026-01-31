from fastapi import status

from app.core.exceptions import AppError, ErrorCode


class AuthError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED


class InvalidCredentialsError(AuthError):
    detail = "Invalid credentials"
    error_code = ErrorCode.INVALID_CREDENTIALS


class TokenExpiredError(AuthError):
    detail = "Token expired"
    error_code = ErrorCode.TOKEN_EXPIRED


class TokenInvalidError(AuthError):
    detail = "Invalid Token"
    error_code = ErrorCode.TOKEN_INVALID


class TokenInvalidTypeError(TokenInvalidError):
    detail = "Token of invalid type"
    error_code = ErrorCode.TOKEN_INVALID_TYPE
