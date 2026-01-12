from dataclasses import dataclass

from app.users.models import User


@dataclass
class AuthDTO:
    access_token: str
    refresh_token: str
    expires_in: int
    user: User
    token_type: str = "bearer"
