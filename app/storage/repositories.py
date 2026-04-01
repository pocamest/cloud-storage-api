import uuid
from collections.abc import Sequence

from sqlalchemy import Text, and_, case, cast, func, literal, select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models import StorageItem
from app.storage.rows import StorageItemWithPathRow, SubtreeNodeRow
from app.storage.types import StorageItemKind, StorageItemT


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

    async def get_path(self, id: uuid.UUID, owner_id: uuid.UUID) -> str | None:
        anchor = select(
            StorageItem.parent_id, StorageItem.name, literal(0).label("level")
        ).where(StorageItem.id == id, StorageItem.owner_id == owner_id)
        cte = anchor.cte("cte", recursive=True)

        recursive_part = select(
            StorageItem.parent_id,
            StorageItem.name,
            (cte.c.level + 1).label("level"),
        ).join(
            cte,
            and_(
                StorageItem.id == cte.c.parent_id,
                StorageItem.owner_id == owner_id,
            ),
        )

        cte = cte.union_all(recursive_part)
        stmt = select(
            "/"
            + func.string_agg(
                cte.c.name,
                aggregate_order_by(literal("/"), cte.c.level.desc()),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_name_with_path(
        self, name_substring: str, owner_id: uuid.UUID
    ) -> list[StorageItemWithPathRow]:
        anchor = select(
            StorageItem.id.label("target_id"),
            StorageItem.parent_id,
            StorageItem.name,
            literal(0).label("level"),
        ).where(
            StorageItem.name.icontains(name_substring), StorageItem.owner_id == owner_id
        )
        cte = anchor.cte("cte", recursive=True)

        recursive_part = select(
            cte.c.target_id,
            StorageItem.parent_id,
            StorageItem.name,
            (cte.c.level + 1).label("level"),
        ).join(
            cte,
            and_(
                StorageItem.id == cte.c.parent_id,
                StorageItem.owner_id == owner_id,
            ),
        )

        cte = cte.union_all(recursive_part)

        path_subq = (
            select(
                cte.c.target_id,
                (
                    "/"
                    + func.string_agg(
                        cte.c.name,
                        aggregate_order_by(literal("/"), cte.c.level.desc()),
                    )
                ).label("path"),
            )
            .group_by(cte.c.target_id)
            .subquery()
        )

        stmt = select(StorageItem, path_subq.c.path).join(
            path_subq, StorageItem.id == path_subq.c.target_id
        )

        result = await self._session.execute(stmt)
        return [StorageItemWithPathRow(*item) for item in result.all()]

    async def get_s3_key_for_all_children(
        self, id: uuid.UUID, owner_id: uuid.UUID
    ) -> Sequence[str]:
        s3_key_column = StorageItem.__table__.c.s3_key
        anchor = select(StorageItem.id, StorageItem.kind, s3_key_column).where(
            StorageItem.id == id, StorageItem.owner_id == owner_id
        )
        cte = anchor.cte("cte", recursive=True)

        recursive_part = select(StorageItem.id, StorageItem.kind, s3_key_column).join(
            cte,
            and_(StorageItem.parent_id == cte.c.id, StorageItem.owner_id == owner_id),
        )

        cte = cte.union_all(recursive_part)

        stmt = select(cte.c.s3_key).where(cte.c.kind == StorageItemKind.FILE)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_ids_for_parents(
        self, id: uuid.UUID, owner_id: uuid.UUID
    ) -> Sequence[uuid.UUID]:
        anchor = select(StorageItem.parent_id).where(
            StorageItem.id == id, StorageItem.owner_id == owner_id
        )

        cte = anchor.cte(name="cte", recursive=True)

        recursive_part = select(StorageItem.parent_id).join(
            cte,
            and_(StorageItem.id == cte.c.parent_id, StorageItem.owner_id == owner_id),
        )

        cte = cte.union_all(recursive_part)

        stmt = select(cte.c.parent_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_subtree(
        self, id: uuid.UUID, owner_id: uuid.UUID
    ) -> list[SubtreeNodeRow]:
        s3_key_column = StorageItem.__table__.c.s3_key
        anchor = select(
            StorageItem.id,
            StorageItem.kind,
            s3_key_column,
            cast(StorageItem.name, Text).label("relative_path"),
        ).where(StorageItem.id == id, StorageItem.owner_id == owner_id)
        cte = anchor.cte("cte", recursive=True)

        recursive_part = select(
            StorageItem.id,
            StorageItem.kind,
            s3_key_column,
            (cte.c.relative_path + "/" + StorageItem.name).label("relative_path"),
        ).join(
            cte,
            and_(StorageItem.parent_id == cte.c.id, StorageItem.owner_id == owner_id),
        )

        cte = cte.union_all(recursive_part)

        final_relative_path = case(
            (cte.c.kind == StorageItemKind.FOLDER, cte.c.relative_path + "/"),
            else_=cte.c.relative_path,
        ).label("relative_path")
        stmt = select(final_relative_path, cte.c.s3_key)
        result = await self._session.execute(stmt)
        return [SubtreeNodeRow(*file) for file in result.all()]
