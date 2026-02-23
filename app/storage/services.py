import uuid

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.storage.adapters import S3Adapter
from app.storage.exceptions import (
    FileNotFoundError,
    FolderNotFoundError,
    NameAlreadyTakenError,
)
from app.storage.models import UNIQUE_NAME_WITHIN_PARENT, File, Folder
from app.storage.repositories import StorageItemRepository
from app.users.models import User


class StorageService:
    def __init__(
        self,
        session: AsyncSession,
        storage_item_repo: StorageItemRepository,
        s3_adapter: S3Adapter,
    ):
        self._session = session
        self._storage_item_repo = storage_item_repo
        self._s3_adapter = s3_adapter
        self._s3_files_prefix = settings.s3_files_prefix

    async def _check_parent_folder_exists(
        self, parent_id: uuid.UUID | None, owner_id: uuid.UUID
    ) -> None:
        if parent_id is None:
            return
        parent = await self._storage_item_repo.find_by_id_and_owner(
            id=parent_id, owner_id=owner_id, model_class=Folder
        )
        if parent is None:
            raise FolderNotFoundError()

    # TODO: нужно разобраться с ограничением на размер файла
    async def upload_file(
        self,
        filename: str | None,
        parent_id: uuid.UUID | None,
        content: bytes,
        owner: User,
    ) -> File:
        await self._check_parent_folder_exists(parent_id=parent_id, owner_id=owner.id)
        name = filename or str(uuid.uuid4())
        # name_exists просто оптимизация, чтобы при дублирующем имени не всегда
        # приходилось записывать файл в s3,
        # но в основном мы полагаемся на ограничение бд UNIQUE_NAME_WITHIN_PARENT
        name_exists_in_folder = await self._storage_item_repo.name_exists(
            name=name, owner_id=owner.id, parent_id=parent_id
        )
        if name_exists_in_folder:
            raise NameAlreadyTakenError()
        file_id = uuid.uuid4()
        s3_key = f"{self._s3_files_prefix}/{owner.id}/{file_id}"
        await self._s3_adapter.upload(key=s3_key, content=content)

        try:
            file = self._storage_item_repo.add(
                File(
                    id=file_id,
                    name=name,
                    owner_id=owner.id,
                    parent_id=parent_id,
                    size=len(content),
                    s3_key=s3_key,
                )
            )

            await self._session.commit()
            # TODO: refresh() если в будущем добавлю поля автогенерируемые поля в бд
            await self._session.refresh(file)
            return file

        except IntegrityError as e:
            await self._session.rollback()
            await self._s3_adapter.delete(s3_key)
            if UNIQUE_NAME_WITHIN_PARENT in str(e.orig):
                raise NameAlreadyTakenError() from e
            raise

        except SQLAlchemyError:
            await self._session.rollback()
            await self._s3_adapter.delete(s3_key)
            raise

    async def get_file(self, id: uuid.UUID, owner: User) -> File:
        file = await self._storage_item_repo.find_by_id_and_owner(
            id=id, owner_id=owner.id, model_class=File
        )
        if file is None:
            raise FileNotFoundError()

        await self._session.refresh(file)
        return file
