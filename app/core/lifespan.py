from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import engine
from app.core.redis import redis_client
from app.core.s3 import s3_provider


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    await s3_provider.init()
    yield

    await engine.dispose()
    await redis_client.aclose()
    await s3_provider.aclose()
