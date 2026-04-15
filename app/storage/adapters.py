from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client
    from types_aiobotocore_s3.type_defs import ObjectIdentifierTypeDef

from app.core.config import settings


class S3Adapter:
    def __init__(self, client: "S3Client", limit_delete: int = 1000) -> None:
        self._client = client
        self._bucket = settings.s3_bucket_name
        self._limit_delete = limit_delete

    async def upload(self, key: str, content: bytes) -> None:
        await self._client.put_object(Bucket=self._bucket, Key=key, Body=content)

    async def delete(self, key: str) -> None:
        await self._client.delete_object(Bucket=self._bucket, Key=key)

    async def download(self, key: str) -> bytes:
        response = await self._client.get_object(Bucket=self._bucket, Key=key)
        async with response["Body"] as stream:
            return await stream.read()

    async def delete_objects(self, keys: Sequence[str]) -> None:
        for i in range(0, len(keys), self._limit_delete):
            objects: list["ObjectIdentifierTypeDef"] = [  # noqa: UP037
                {"Key": key} for key in keys[i : i + self._limit_delete]
            ]
            await self._client.delete_objects(
                Bucket=self._bucket, Delete={"Objects": objects, "Quiet": True}
            )
