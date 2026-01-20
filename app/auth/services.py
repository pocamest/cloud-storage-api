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

    def _decode_token(self, token: str) -> JWTPayload:
        try:
            payload: JWTPayload = jwt.decode(
                jwt=token, key=self.secret_key, algorithms=[self.algorithm]
            )
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError() from e

        except jwt.InvalidTokenError as e:
            raise TokenInvalidError() from e

        return payload

    def create_access_token(self, user_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        exp = now + timedelta(seconds=(self.access_token_exp_seconds))
        payload: JWTPayload = {
            "sub": str(user_id),
            "type": TokenType.ACCESS,
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
        }
        return jwt.encode(
            payload=cast(dict[str, Any], payload),
            key=self.secret_key,
            algorithm=self.algorithm,
        )

    async def create_refresh_token(self, user_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        jti = str(uuid.uuid4())
        exp = now + timedelta(seconds=(self.refresh_token_exp_seconds))
        sub = str(user_id)
        payload: JWTPayload = {
            "sub": sub,
            "type": TokenType.REFRESH,
            "jti": jti,
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
        }

        await self.token_repo.save(
            token_type=TokenType.REFRESH,
            token_id=jti,
            value=sub,
            exp_seconds=self.refresh_token_exp_seconds,
        )

        return jwt.encode(
            payload=cast(dict[str, Any], payload),
            key=self.secret_key,
            algorithm=self.algorithm,
        )

    def verify_access_token(self, token: str) -> uuid.UUID:
        payload = self._decode_token(token)

        if payload["type"] != TokenType.ACCESS:
            raise TokenInvalidError(detail="Expected only access token")

        user_id = uuid.UUID(payload["sub"])

        return user_id

    async def verify_refresh_token(self, token: str) -> uuid.UUID:
        payload = self._decode_token(token)

        if payload["type"] != TokenType.REFRESH:
            raise TokenInvalidError(detail="Expected only refresh token")

        jti = payload["jti"]
        if not await self.token_repo.exists(token_type=TokenType.REFRESH, token_id=jti):
            raise TokenExpiredError()

        user_id = uuid.UUID(payload["sub"])

        return user_id

    async def revoke_refresh_token(self, token: str) -> None:
        payload = self._decode_token(token)
        if payload["type"] != TokenType.REFRESH:
            raise TokenInvalidError(detail="Expected only refresh token")

        jti = payload["jti"]

        await self.token_repo.delete(token_type=TokenType.REFRESH, token_id=jti)


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

    async def get_user_from_access_token(self, token: str) -> User:
        user_id = self.token_service.verify_access_token(token)

        try:
            user = await self.user_service.get_by_id(user_id)
        except UserNotFoundError as e:
            raise TokenInvalidError() from e

        return user

    async def refresh(self, refresh_token: str) -> TokenDTO:
        user_id = await self.token_service.verify_refresh_token(refresh_token)

        access_token = self.token_service.create_access_token(user_id)

        return TokenDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.token_service.access_token_exp_seconds,
        )

    async def logout(self, refresh_token: str) -> None:
        await self.token_service.revoke_refresh_token(refresh_token)
