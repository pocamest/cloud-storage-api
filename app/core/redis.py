from redis.asyncio import Redis

from app.core.config import settings

redis_client: Redis = Redis.from_url(url=settings.redis_url, decode_responses=True)
