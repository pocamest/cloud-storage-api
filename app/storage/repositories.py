import uuid
from collections.abc import Sequence
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import with_polymorphic

from app.storage.models import StorageItem

StorageItemT = TypeVar("StorageItemT", bound=StorageItem)


class StorageItemRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def add(self, storage_item: StorageItemT) -> StorageItemT:
        self._session.add(storage_item)
        return storage_item

    async def find_by_id_and_owner(
        self, id: uuid.UUID, owner_id: uuid.UUID, model_class: type[StorageItemT]
    ) -> StorageItemT | None:
        stmt = select(model_class).where(
            model_class.id == id, model_class.owner_id == owner_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def name_exists(
        self, name: str, owner_id: uuid.UUID, parent_id: uuid.UUID | None
    ) -> bool:
        stmt = select(StorageItem.id).where(
            StorageItem.name == name,
            StorageItem.owner_id == owner_id,
            StorageItem.parent_id == parent_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def delete(self, storage_item: StorageItem) -> None:
        await self._session.delete(storage_item)

    async def find_by_parent_and_owner(
        self, owner_id: uuid.UUID, parent_id: uuid.UUID | None
    ) -> Sequence[StorageItem]:
        # сразу загружает поля наследников, потому что lazy_load в async не работает
        full_storage_item = with_polymorphic(StorageItem, "*")
        stmt = select(full_storage_item).where(
            full_storage_item.owner_id == owner_id,
            full_storage_item.parent_id == parent_id,
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
