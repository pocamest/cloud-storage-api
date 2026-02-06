from contextlib import AsyncExitStack

from aiobotocore.session import get_session
from types_aiobotocore_s3 import S3Client

from app.core.config import settings


class S3Provider:
    def __init__(self) -> None:
        self._exit_stack = AsyncExitStack()
        self._client: S3Client | None = None

    async def init(self) -> None:
        if self._client is not None:
            return
        session = get_session()
        self._client = await self._exit_stack.enter_async_context(
            session.create_client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
            )
        )

    @property
    def client(self) -> S3Client:
        if self._client is None:
            raise RuntimeError("S3 is not initialized")
        return self._client

    async def aclose(self) -> None:
        await self._exit_stack.aclose()
        self._client = None


s3_provider = S3Provider()
