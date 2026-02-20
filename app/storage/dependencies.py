from typing import Annotated

from fastapi import Depends

from app.core.dependencies import S3ClientDep, SessionDep
from app.storage.adapters import S3Adapter
from app.storage.repositories import StorageItemRepository
from app.storage.services import StorageService


async def get_storage_item_repository(session: SessionDep) -> StorageItemRepository:
    return StorageItemRepository(session)


StorageItemRepositoryDep = Annotated[
    StorageItemRepository, Depends(get_storage_item_repository)
]


async def get_s3_adapter(s3_client: S3ClientDep) -> S3Adapter:
    return S3Adapter(s3_client)


S3AdapterDep = Annotated[S3Adapter, Depends(get_s3_adapter)]


async def get_storage_service(
    session: SessionDep,
    storage_item_repo: StorageItemRepositoryDep,
    s3_adapter: S3AdapterDep,
) -> StorageService:
    return StorageService(
        session=session, storage_item_repo=storage_item_repo, s3_adapter=s3_adapter
    )


StorageServiceDep = Annotated[StorageService, Depends(get_storage_service)]
