import pytest
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.infra
async def test_infrastructure_is_ready(
    session: AsyncSession,
    redis_client: Redis,
) -> None:
    result = await session.execute(text("SELECT 1"))
    assert result.scalar() == 1

    await redis_client.set("check", "ok")
    assert await redis_client.get("check") == "ok"
