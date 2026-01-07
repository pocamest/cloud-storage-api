from app.core.exceptions import AppError


class UserError(AppError):
    pass


class UserAlreadyExistsError(UserError):
    status_code = 409
    detail = "User already exists"
