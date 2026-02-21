import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def create(self, user: User) -> User:
        self._session.add(user)
        return user

    async def find_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id(self, id: uuid.UUID) -> User | None:
        return await self._session.get(User, id)
