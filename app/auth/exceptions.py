from app.core.exceptions import AppError


class AuthError(AppError):
    pass


class InvalidCredentialsError(AuthError):
    status_code = 401
    detail = "Invalid credentials"
