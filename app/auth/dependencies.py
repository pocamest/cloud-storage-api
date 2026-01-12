from typing import Annotated

from fastapi import Depends

from app.auth.repositories import TokenRepository
from app.auth.services import AuthService, TokenService
from app.core.config import settings
from app.core.dependencies import RedisDep
from app.users.dependencies import UserServiceDep


async def get_token_repo(redis_client: RedisDep) -> TokenRepository:
    return TokenRepository(redis_client=redis_client)


TokenRepositoryDep = Annotated[TokenRepository, Depends(get_token_repo)]


async def get_token_service(token_repo: TokenRepositoryDep) -> TokenService:
    return TokenService(
        token_repo=token_repo,
        secret_key=settings.token_secret_key,
        algorithm=settings.token_algorithm,
        access_token_exp_minutes=settings.access_token_exp_minutes,
        refresh_token_exp_days=settings.refresh_token_exp_days,
    )


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


async def get_auth_service(
    user_service: UserServiceDep, token_service: TokenServiceDep
) -> AuthService:
    return AuthService(user_service=user_service, token_service=token_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
