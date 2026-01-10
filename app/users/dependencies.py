from typing import Annotated

from fastapi import Depends

from app.core.dependencies import SessionDep
from app.users.repositories import UserRepository
from app.users.services import UserService


async def get_user_repo(session: SessionDep) -> UserRepository:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repo)]


async def get_user_service(
    session: SessionDep, user_repo: UserRepositoryDep
) -> UserService:
    return UserService(session=session, user_repo=user_repo)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
