from datetime import datetime
from enum import StrEnum
from typing import NotRequired, TypedDict


class JWTPayload(TypedDict):
    sub: str
    type: str
    exp: datetime
    iat: datetime
    jti: NotRequired[str]


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
