import uuid

from redis.asyncio import Redis


class TokenRepository:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    def _get_refresh_token_key(self, jti: str) -> str:
        return f"refresh_token:{jti}"

    async def save_refresh_token(
        self, user_id: uuid.UUID, jti: str, exp_seconds: int
    ) -> None:
        key = self._get_refresh_token_key(jti)
        await self.redis_client.set(key, str(user_id), ex=exp_seconds)

    async def find_user_id(self, jti: str) -> str | None:
        key = self._get_refresh_token_key(jti)
        result: str | None = await self.redis_client.get(key)
        return result

    async def delete_refresh_token(self, jti: str) -> None:
        key = self._get_refresh_token_key(jti)
        await self.redis_client.delete(key)
