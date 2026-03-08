import uuid

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.storage.adapters import S3Adapter
from app.storage.dtos import DownloadFileDTO, FileDTO, FolderDTO
from app.storage.exceptions import (
    FileNotFoundError,
    FolderNotFoundError,
    NameAlreadyTakenError,
)
from app.storage.models import UNIQUE_NAME_WITHIN_PARENT, File, Folder, StorageItem
from app.storage.repositories import StorageItemRepository
from app.users.models import User


# TODO: становится много хелперов, видимо нужен будет отдельный доменный сервис
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

    async def _check_folder_exists(
        self, id: uuid.UUID | None, owner_id: uuid.UUID
    ) -> None:
        if id is None:
            return
        parent = await self._storage_item_repo.find_by_id_and_owner(
            id=id, owner_id=owner_id, model_class=Folder
        )
        if parent is None:
            raise FolderNotFoundError()

    async def _check_name_not_exists_in_parent(
        self, name: str, parent_id: uuid.UUID | None, owner_id: uuid.UUID
    ) -> None:
        name_exists_in_parent = await self._storage_item_repo.name_exists(
            name=name, owner_id=owner_id, parent_id=parent_id
        )
        if name_exists_in_parent:
            raise NameAlreadyTakenError()

    async def _build_path(self, id: uuid.UUID | None, owner_id: uuid.UUID) -> str:
        root = "/"
        if id is None:
            return root
        items = await self._storage_item_repo.get_names_for_self_and_parents(
            id=id, owner_id=owner_id
        )

        # TODO: по идеи в пути для папки в конце должен быть "/", или так оставлю
        path = "/".join(items)
        return f"{root}{path}"

    def _map_file_to_dto(self, file: File, path: str) -> FileDTO:
        return FileDTO(
            id=file.id,
            name=file.name,
            owner_id=file.owner_id,
            parent_id=file.parent_id,
            size=file.size,
            path=path,
        )

    def _map_folder_to_dto(self, folder: Folder, path: str) -> FolderDTO:
        return FolderDTO(
            id=folder.id,
            name=folder.name,
            owner_id=folder.owner_id,
            parent_id=folder.parent_id,
            path=path,
        )

    def _map_to_dto(self, item: StorageItem, path: str) -> FileDTO | FolderDTO:
        if isinstance(item, File):
            return self._map_file_to_dto(file=item, path=path)
        if isinstance(item, Folder):
            return self._map_folder_to_dto(folder=item, path=path)

        raise ValueError(f"Invalid kind: {item}")

    # TODO: нужно разобраться с ограничением на размер файла
    async def upload_file(
        self,
        filename: str | None,
        parent_id: uuid.UUID | None,
        content: bytes,
        owner: User,
    ) -> FileDTO:
        await self._check_folder_exists(id=parent_id, owner_id=owner.id)
        name = filename or str(uuid.uuid4())
        await self._check_name_not_exists_in_parent(
            name=name, parent_id=parent_id, owner_id=owner.id
        )

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

            path = await self._build_path(id=file.id, owner_id=file.owner_id)

            return self._map_file_to_dto(file=file, path=path)

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

    async def get_file(self, id: uuid.UUID, owner: User) -> FileDTO:
        file = await self._storage_item_repo.find_by_id_and_owner(
            id=id, owner_id=owner.id, model_class=File
        )
        if file is None:
            raise FileNotFoundError()

        path = await self._build_path(id=file.id, owner_id=file.owner_id)

        return self._map_file_to_dto(file=file, path=path)

    async def delete_file(self, id: uuid.UUID, owner: User) -> None:
        file = await self._storage_item_repo.find_by_id_and_owner(
            id=id, owner_id=owner.id, model_class=File
        )
        if file is None:
            raise FileNotFoundError()

        s3_key = file.s3_key

        await self._storage_item_repo.delete(file)
        await self._session.commit()

        await self._s3_adapter.delete(s3_key)

    async def download_file(self, id: uuid.UUID, owner: User) -> DownloadFileDTO:
        file = await self._storage_item_repo.find_by_id_and_owner(
            id=id, owner_id=owner.id, model_class=File
        )
        if file is None:
            raise FileNotFoundError()

        content = await self._s3_adapter.download(key=file.s3_key)
        return DownloadFileDTO(filename=file.name, content=content)

    async def create_folder(
        self, name: str, parent_id: uuid.UUID | None, owner: User
    ) -> FolderDTO:
        await self._check_folder_exists(id=parent_id, owner_id=owner.id)
        await self._check_name_not_exists_in_parent(
            name=name, parent_id=parent_id, owner_id=owner.id
        )

        id = uuid.uuid4()
        try:
            folder = self._storage_item_repo.add(
                Folder(id=id, name=name, owner_id=owner.id, parent_id=parent_id)
            )

            await self._session.commit()

            path = await self._build_path(id=folder.id, owner_id=folder.owner_id)

            return self._map_folder_to_dto(folder=folder, path=path)

        except IntegrityError as e:
            await self._session.rollback()
            if UNIQUE_NAME_WITHIN_PARENT in str(e.orig):
                raise NameAlreadyTakenError() from e
            raise

    async def get_folder(self, id: uuid.UUID, owner: User) -> FolderDTO:
        folder = await self._storage_item_repo.find_by_id_and_owner(
            id=id, owner_id=owner.id, model_class=Folder
        )
        if folder is None:
            raise FolderNotFoundError()

        path = await self._build_path(id=folder.id, owner_id=folder.owner_id)

        return self._map_folder_to_dto(folder=folder, path=path)

    async def get_folder_items(
        self, id: uuid.UUID | None, owner: User
    ) -> list[FileDTO | FolderDTO]:
        await self._check_folder_exists(id=id, owner_id=owner.id)

        items = await self._storage_item_repo.find_by_parent_and_owner(
            owner_id=owner.id, parent_id=id
        )

        result: list[FileDTO | FolderDTO] = []

        base_path = await self._build_path(id=id, owner_id=owner.id)
        # TODO: пока такой костыль, по-другому не придумал как собирать путь
        base_path = "" if base_path == "/" else base_path

        for item in items:
            path = f"{base_path}/{item.name}"
            result.append(self._map_to_dto(item=item, path=path))

        return result

    async def get_root_items(self, owner: User) -> list[FileDTO | FolderDTO]:
        return await self.get_folder_items(id=None, owner=owner)

    async def search(self, query: str, owner: User) -> list[FileDTO | FolderDTO]:
        items = await self._storage_item_repo.find_by_name_substring(
            name_substring=query, owner_id=owner.id
        )

        result: list[FileDTO | FolderDTO] = []

        for item in items:
            path = await self._build_path(id=item.id, owner_id=item.owner_id)
            result.append(self._map_to_dto(item=item, path=path))

        return result
