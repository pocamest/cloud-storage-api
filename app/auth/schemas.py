from pydantic import BaseModel, EmailStr

from app.users.schemes import UserRead


class AuthCreate(BaseModel):
    email: EmailStr
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
