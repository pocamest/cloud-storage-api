from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import S3Client

from app.core.database import session_factory
from app.core.redis import redis_client
from app.core.s3 import s3_provider


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_redis_client() -> Redis:
    return redis_client


RedisDep = Annotated[Redis, Depends(get_redis_client)]


async def get_s3_client() -> S3Client:
    return s3_provider.client


S3ClientDep = Annotated[S3Client, Depends(get_s3_client)]
