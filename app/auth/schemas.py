from pydantic import BaseModel

from app.users.schemas import UserRead
from app.users.types import NormalizedEmail


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
