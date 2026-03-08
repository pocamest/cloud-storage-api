import uuid
from collections.abc import Sequence
from typing import TypeVar

from sqlalchemy import and_, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

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
        stmt = select(StorageItem).where(
            StorageItem.owner_id == owner_id,
            StorageItem.parent_id == parent_id,
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    # TODO: Проверить синтаксис и отрефакторить
    async def get_names_for_self_and_parents(
        self, id: uuid.UUID, owner_id: uuid.UUID
    ) -> Sequence[str]:
        anchor = select(
            StorageItem.parent_id, StorageItem.name, literal(0).label("level")
        ).where(StorageItem.id == id, StorageItem.owner_id == owner_id)
        cte = anchor.cte("cte", recursive=True)

        recursive_part = select(
            StorageItem.parent_id, StorageItem.name, cte.c.level + 1
        ).join(
            cte,
            and_(
                StorageItem.id == cte.c.parent_id,
                StorageItem.owner_id == owner_id,
            ),
        )

        cte = cte.union_all(recursive_part)

        stmt = select(cte.c.name).order_by(cte.c.level.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def find_by_name_substring(
        self, name_substring: str, owner_id: uuid.UUID
    ) -> Sequence[StorageItem]:
        stmt = select(StorageItem).where(
            StorageItem.name.icontains(name_substring),
            StorageItem.owner_id == owner_id,
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
