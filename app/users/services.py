from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.users.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.users.models import User
from app.users.repositories import UserRepository
from app.users.schemes import UserCreate


class UserService:
    def __init__(self, session: AsyncSession, user_repo: UserRepository):
        self.session = session
        self.user_repo = user_repo

    async def create_user(self, user_data: UserCreate) -> User:
        if await self.user_repo.find_by_email(user_data.email) is not None:
            raise UserAlreadyExistsError()

        password_hash = hash_password(user_data.password)
        created_user = self.user_repo.create(
            User(email=user_data.email, password_hash=password_hash)
        )

        await self.session.commit()
        await self.session.refresh(created_user)

        return created_user

    async def find_by_credentials(self, email: str, password: str) -> User | None:
        user = await self.user_repo.find_by_email(email)

        if user is None:
            return None

        if not verify_password(raw_password=password, password_hash=user.password_hash):
            return None

        return user

    async def get_by_id(self, id: int) -> User:
        user = await self.user_repo.find_by_id(id)

        if user is None:
            raise UserNotFoundError()

        return user
