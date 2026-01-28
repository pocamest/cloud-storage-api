from pydantic import BaseModel

from app.core.types import NormalizedEmail
from app.users.schemas import UserRead


class AuthCreate(BaseModel):
    email: NormalizedEmail
    password: str


class TokenRead(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class AuthRefresh(BaseModel):
    refresh_token: str


class AuthRead(TokenRead):
    user: UserRead
