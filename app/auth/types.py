from enum import StrEnum
from typing import NotRequired, TypedDict


class JWTPayload(TypedDict):
    sub: str
    type: str
    exp: int
    iat: int
    jti: NotRequired[str]


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
