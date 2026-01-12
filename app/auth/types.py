from datetime import datetime
from typing import NotRequired, TypedDict


class JWTPayload(TypedDict):
    sub: str
    type: str
    exp: datetime
    iat: datetime
    jti: NotRequired[str]
