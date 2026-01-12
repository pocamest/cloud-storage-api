import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt

from app.auth.dtos import AuthDTO
from app.auth.exceptions import InvalidCredentialsError
from app.auth.repositories import TokenRepository
from app.auth.schemas import AuthCreate
from app.auth.types import JWTPayload
from app.users.services import UserService


class TokenService:
    def __init__(
        self,
        token_repo: TokenRepository,
        secret_key: str,
        algorithm: str,
        access_token_exp_minutes: int,
        refresh_token_exp_days: int,
    ):
        self.token_repo = token_repo
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_exp_minutes = access_token_exp_minutes
        self.refresh_token_exp_days = refresh_token_exp_days

    def create_access_token(self, user_id: int) -> str:
        now = datetime.now(UTC)
        exp = now + timedelta(minutes=(self.access_token_exp_minutes))
        payload: JWTPayload = {
            "sub": str(user_id),
            "type": "access",
            "exp": exp,
            "iat": now,
        }
        return jwt.encode(
            payload=cast(dict[str, Any], payload),
            key=self.secret_key,
            algorithm=self.algorithm,
        )

    async def create_refresh_token(self, user_id: int) -> str:
        now = datetime.now(UTC)
        jti = str(uuid.uuid4())
        delta = timedelta(days=(self.refresh_token_exp_days))
        exp = now + delta
        payload: JWTPayload = {
            "sub": str(user_id),
            "type": "refresh",
            "jti": jti,
            "exp": exp,
            "iat": now,
        }

        exp_seconds = int(delta.total_seconds())

        await self.token_repo.save_refresh_token(
            user_id=user_id, jti=jti, exp_seconds=exp_seconds
        )

        return jwt.encode(
            payload=cast(dict[str, Any], payload),
            key=self.secret_key,
            algorithm=self.algorithm,
        )


class AuthService:
    def __init__(self, user_service: UserService, token_service: TokenService):
        self.user_service = user_service
        self.token_service = token_service

    async def login(self, auth_data: AuthCreate) -> AuthDTO:
        user = await self.user_service.find_by_credentials(
            email=auth_data.email, password=auth_data.password
        )

        if user is None:
            raise InvalidCredentialsError()

        user_id = user.id
        access_token = self.token_service.create_access_token(user_id)
        refresh_token = await self.token_service.create_refresh_token(user_id)

        expires_in = self.token_service.access_token_exp_minutes * 60

        return AuthDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user=user,
        )
