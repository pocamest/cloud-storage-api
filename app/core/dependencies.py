from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import session_factory
from app.core.redis import redis_client


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_redis_client() -> Redis:
    return redis_client


RedisDep = Annotated[Redis, Depends(get_redis_client)]
