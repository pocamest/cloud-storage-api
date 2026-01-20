from redis.asyncio import Redis

from app.auth.types import TokenType


class TokenRepository:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    def _create_key(self, token_type: TokenType, token_id: str) -> str:
        return f"{token_type}:{token_id}"

    async def save(
        self, token_type: TokenType, token_id: str, value: str, exp_seconds: int
    ) -> None:
        key = self._create_key(token_type, token_id)
        await self.redis_client.set(key, value, ex=exp_seconds)

    async def exists(self, token_type: TokenType, token_id: str) -> bool:
        key = self._create_key(token_type, token_id)
        result: int = await self.redis_client.exists(key)
        return result > 0

    async def delete(self, token_type: TokenType, token_id: str) -> None:
        key = self._create_key(token_type, token_id)
        await self.redis_client.delete(key)
