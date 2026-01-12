from redis.asyncio import Redis


class TokenRepository:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    def _get_refresh_token_key(self, jti: str) -> str:
        return f"refresh_token:{jti}"

    async def save_refresh_token(
        self, user_id: int, jti: str, exp_seconds: int
    ) -> None:
        key = self._get_refresh_token_key(jti)
        await self.redis_client.set(key, user_id, ex=exp_seconds)
