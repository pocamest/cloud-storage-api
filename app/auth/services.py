import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt

from app.auth.dtos import AuthDTO, TokenDTO
from app.auth.exceptions import (
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    TokenInvalidTypeError,
)
from app.auth.repositories import TokenRepository
from app.auth.schemas import LoginRequest
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
        self._token_repo = token_repo
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_exp_seconds = access_token_exp_minutes * 60
        self._refresh_token_exp_seconds = refresh_token_exp_days * 86400

    def _decode_token(self, token: str) -> JWTPayload:
        try:
            payload: JWTPayload = jwt.decode(
                jwt=token, key=self._secret_key, algorithms=[self._algorithm]
            )
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError() from e

        except jwt.InvalidTokenError as e:
            raise TokenInvalidError() from e

        return payload

    def create_access_token(self, user_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        exp = now + timedelta(seconds=(self._access_token_exp_seconds))
        payload: JWTPayload = {
            "sub": str(user_id),
            "type": TokenType.ACCESS,
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
        }
        return jwt.encode(
            payload=cast(dict[str, Any], payload),
            key=self._secret_key,
            algorithm=self._algorithm,
        )

    async def create_refresh_token(self, user_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        jti = str(uuid.uuid4())
        exp = now + timedelta(seconds=(self._refresh_token_exp_seconds))
        sub = str(user_id)
        payload: JWTPayload = {
            "sub": sub,
            "type": TokenType.REFRESH,
            "jti": jti,
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
        }

        await self._token_repo.save(
            token_type=TokenType.REFRESH,
            token_id=jti,
            value=sub,
            exp_seconds=self._refresh_token_exp_seconds,
        )

        return jwt.encode(
            payload=cast(dict[str, Any], payload),
            key=self._secret_key,
            algorithm=self._algorithm,
        )

    def verify_access_token(self, token: str) -> uuid.UUID:
        payload = self._decode_token(token)

        if payload["type"] != TokenType.ACCESS:
            raise TokenInvalidTypeError()

        user_id = uuid.UUID(payload["sub"])

        return user_id

    async def verify_refresh_token(self, token: str) -> uuid.UUID:
        payload = self._decode_token(token)

        if payload["type"] != TokenType.REFRESH:
            raise TokenInvalidTypeError()

        jti = payload["jti"]
        if not await self._token_repo.exists(
            token_type=TokenType.REFRESH, token_id=jti
        ):
            raise TokenExpiredError()

        user_id = uuid.UUID(payload["sub"])

        return user_id

    async def revoke_refresh_token(self, token: str) -> None:
        payload = self._decode_token(token)
        if payload["type"] != TokenType.REFRESH:
            raise TokenInvalidTypeError()

        jti = payload["jti"]

        await self._token_repo.delete(token_type=TokenType.REFRESH, token_id=jti)


class AuthService:
    def __init__(self, user_service: UserService, token_service: TokenService):
        self._user_service = user_service
        self._token_service = token_service

    async def _create_tokens(self, user: User) -> AuthDTO:
        user_id = user.id
        access_token = self._token_service.create_access_token(user_id)
        refresh_token = await self._token_service.create_refresh_token(user_id)

        return AuthDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._token_service._access_token_exp_seconds,
            user=user,
        )

    async def login(self, auth_data: LoginRequest) -> AuthDTO:
        user = await self._user_service.find_by_credentials(
            email=auth_data.email, password=auth_data.password
        )

        if user is None:
            raise InvalidCredentialsError()

        return await self._create_tokens(user)

    async def register(self, user_data: UserCreate) -> AuthDTO:
        user = await self._user_service.create_user(user_data)
        return await self._create_tokens(user)

    async def get_user_from_access_token(self, token: str) -> User:
        user_id = self._token_service.verify_access_token(token)

        try:
            user = await self._user_service.get_by_id(user_id)
        except UserNotFoundError as e:
            raise TokenInvalidError() from e

        return user

    async def refresh(self, refresh_token: str) -> TokenDTO:
        user_id = await self._token_service.verify_refresh_token(refresh_token)

        access_token = self._token_service.create_access_token(user_id)

        return TokenDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._token_service._access_token_exp_seconds,
        )

    async def logout(self, refresh_token: str) -> None:
        await self._token_service.revoke_refresh_token(refresh_token)
