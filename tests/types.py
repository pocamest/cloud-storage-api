from typing import Protocol

from app.users.models import User


class CreateUserCallable(Protocol):
    async def __call__(
        self, email: str = "test@example.com", password: str = "test_password"
    ) -> User: ...
