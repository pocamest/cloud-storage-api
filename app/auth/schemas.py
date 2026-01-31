from pydantic import BaseModel

from app.core.types import NormalizedEmail
from app.users.schemas import UserRead


class LoginRequest(BaseModel):
    email: NormalizedEmail
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class LoginResponse(TokenResponse):
    user: UserRead


class RefreshRequest(BaseModel):
    refresh_token: str
