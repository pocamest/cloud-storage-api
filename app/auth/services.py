import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt

from app.auth.dtos import AuthDTO, TokenDTO
from app.auth.exceptions import (
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
)
from app.auth.repositories import TokenRepository
from app.auth.schemas import AuthCreate
from app.auth.types import JWTPayload, TokenType
from app.users.exceptions import UserNotFoundError
from app.users.models import User
from app.users.schemas import UserCreate
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
        self.access_token_exp_seconds = access_token_exp_minutes * 60
        self.refresh_token_exp_seconds = refresh_token_exp_days * 86400

    def create_access_token(self, user_id: int) -> str:
        now = datetime.now(UTC)
        exp = now + timedelta(seconds=(self.access_token_exp_seconds))
        payload: JWTPayload = {
            "sub": str(user_id),
            "type": TokenType.ACCESS,
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
        exp = now + timedelta(seconds=(self.refresh_token_exp_seconds))
        payload: JWTPayload = {
            "sub": str(user_id),
            "type": TokenType.REFRESH,
            "jti": jti,
            "exp": exp,
            "iat": now,
        }

        await self.token_repo.save_refresh_token(
            user_id=user_id, jti=jti, exp_seconds=self.refresh_token_exp_seconds
        )

        return jwt.encode(
            payload=cast(dict[str, Any], payload),
            key=self.secret_key,
            algorithm=self.algorithm,
        )

    def verify_token(self, token: str) -> JWTPayload:
        try:
            payload: JWTPayload = jwt.decode(
                jwt=token, key=self.secret_key, algorithms=[self.algorithm]
            )
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError() from e

        except jwt.InvalidTokenError as e:
            raise TokenInvalidError() from e

        return payload

    async def get_user_id_from_refresh_token(self, payload: JWTPayload) -> int:
        if payload["type"] != TokenType.REFRESH:
            raise TokenInvalidError(detail="Expected only refresh token")

        jti = payload["jti"]
        user_id = await self.token_repo.find_user_id(jti)

        if user_id is None:
            raise TokenExpiredError()

        return int(user_id)


class AuthService:
    def __init__(self, user_service: UserService, token_service: TokenService):
        self.user_service = user_service
        self.token_service = token_service

    async def _create_tokens(self, user: User) -> AuthDTO:
        user_id = user.id
        access_token = self.token_service.create_access_token(user_id)
        refresh_token = await self.token_service.create_refresh_token(user_id)

        return AuthDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.token_service.access_token_exp_seconds,
            user=user,
        )

    async def login(self, auth_data: AuthCreate) -> AuthDTO:
        user = await self.user_service.find_by_credentials(
            email=auth_data.email, password=auth_data.password
        )

        if user is None:
            raise InvalidCredentialsError()

        return await self._create_tokens(user)

    async def register(self, user_data: UserCreate) -> AuthDTO:
        user = await self.user_service.create_user(user_data)
        return await self._create_tokens(user)

    async def get_user_by_token(self, token: str) -> User:
        payload = self.token_service.verify_token(token)
        user_id = int(payload["sub"])

        try:
            user = await self.user_service.get_by_id(user_id)
        except UserNotFoundError as e:
            raise TokenInvalidError() from e

        return user

    async def refresh(self, refresh_token: str) -> TokenDTO:
        payload = self.token_service.verify_token(refresh_token)
        user_id = await self.token_service.get_user_id_from_refresh_token(payload)

        access_token = self.token_service.create_access_token(user_id)

        return TokenDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.token_service.access_token_exp_seconds,
        )
