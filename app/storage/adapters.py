from types_aiobotocore_s3 import S3Client

from app.core.config import settings


class S3Adapter:
    def __init__(self, client: S3Client) -> None:
        self._client = client
        self._bucket = settings.s3_bucket_name

    async def upload(self, key: str, content: bytes) -> None:
        await self._client.put_object(Bucket=self._bucket, Key=key, Body=content)

    async def delete(self, key: str) -> None:
        await self._client.delete_object(Bucket=self._bucket, Key=key)

    async def download(self, key: str) -> bytes:
        response = await self._client.get_object(Bucket=self._bucket, Key=key)
        async with response["Body"] as stream:
            return await stream.read()
