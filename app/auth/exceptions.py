from app.core.exceptions import AppError


class AuthError(AppError):
    pass


class InvalidCredentialsError(AuthError):
    status_code = 401
    detail = "Invalid credentials"


class TokenExpiredError(AuthError):
    status_code = 401
    detail = "Token expired"


class TokenInvalidError(AuthError):
    status_code = 401
    detail = "Invalid Token"
