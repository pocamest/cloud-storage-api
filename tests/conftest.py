from collections.abc import AsyncGenerator, Awaitable, Callable, Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import AsyncRedisContainer

from app.core.database import Base
from app.core.dependencies import get_redis_client, get_session
from app.core.security import hash_password
from app.main import app
from app.users.models import User  # noqa

POSTGRES_IMAGE = "postgres:18-alpine"
REDIS_IMAGE = "redis:8-alpine"


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer]:
    with PostgresContainer(POSTGRES_IMAGE, driver="asyncpg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def db_url(postgres_container: PostgresContainer) -> str:
    result: str = postgres_container.get_connection_url()
    return result


@pytest.fixture(scope="session")
def apply_migrations(db_url: str) -> None:
    root_dir = Path(__file__).resolve().parent.parent
    alembic_ini_path = root_dir / "alembic.ini"

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    alembic_cfg.attributes["is_test_run"] = True

    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
async def engine(db_url: str, apply_migrations: None) -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(db_url)
    yield engine

    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture(scope="session")
def redis_container() -> Generator[AsyncRedisContainer]:
    with AsyncRedisContainer(REDIS_IMAGE) as redis:
        yield redis


@pytest.fixture(scope="session")
async def redis_connection(
    redis_container: AsyncRedisContainer,
) -> AsyncGenerator[Redis]:
    redis_client = await redis_container.get_async_client(decode_responses=True)
    yield redis_client


@pytest.fixture
async def redis_client(redis_connection: Redis) -> AsyncGenerator[Redis]:
    yield redis_connection
    await redis_connection.flushall()


@pytest.fixture
def override_dependencies(
    session: AsyncSession, redis_client: Redis
) -> Generator[None]:
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_redis_client] = lambda: redis_client
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(override_dependencies: None) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


CreateUserCallable = Callable[[str, str], Awaitable[User]]


@pytest.fixture
async def create_user(
    session: AsyncSession,
) -> CreateUserCallable:
    async def _create_user(
        email: str = "test@example.com", password: str = "test_password"
    ) -> User:
        user = User(email=email, password_hash=hash_password(password))
        session.add(user)

        await session.commit()
        await session.refresh(user)

        return user

    return _create_user
