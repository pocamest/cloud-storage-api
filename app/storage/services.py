import io
import posixpath
import uuid
import zipfile

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.storage.adapters import S3Adapter
from app.storage.constants import ROOT_PATH, UNIQUE_NAME_WITHIN_PARENT
from app.storage.dtos import DownloadFileDTO, DownloadFolderDTO, FileDTO, FolderDTO
from app.storage.exceptions import (
    FileNotFoundError,
    FolderNotFoundError,
    FolderTargetIsSelf,
    FolderTargetIsSubfolder,
    FolderTooLargeToDownloadError,
    NameAlreadyTakenError,
)
from app.storage.models import File, Folder, StorageItem
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

    async def _fetch_file(self, id: uuid.UUID, owner_id: uuid.UUID) -> File:
        file = await self._storage_item_repo.find_by_id_and_owner(
            id=id, owner_id=owner_id, model_class=File
        )
        if file is None:
            raise FileNotFoundError()

        return file

    async def _fetch_folder(self, id: uuid.UUID, owner_id: uuid.UUID) -> Folder:
        folder = await self._storage_item_repo.find_by_id_and_owner(
            id=id, owner_id=owner_id, model_class=Folder
        )
        if folder is None:
            raise FolderNotFoundError()

        return folder

    async def _check_name_not_exists_in_parent(
        self, name: str, parent_id: uuid.UUID | None, owner_id: uuid.UUID
    ) -> None:
        """
        Не гарантирует уникальность из-за состояния гонки при параллельных запросах.
        Используется только для оптимизации перед затратными операциями.
        Основная защита это ограничение  UNIQUE_NAME_WITHIN_PARENT на уровне БД
        """
        name_exists_in_parent = await self._storage_item_repo.name_exists(
            name=name, owner_id=owner_id, parent_id=parent_id
        )
        if name_exists_in_parent:
            raise NameAlreadyTakenError()

    async def _check_target_is_not_subfolder(
        self, id: uuid.UUID, new_parent_id: uuid.UUID, owner_id: uuid.UUID
    ) -> None:
        parents = await self._storage_item_repo.get_ids_for_parents(
            id=new_parent_id, owner_id=owner_id
        )
        if id in parents:
            raise FolderTargetIsSubfolder()

    async def _get_base_path(self, id: uuid.UUID | None, owner_id: uuid.UUID) -> str:
        if id is not None:
            parent_path = await self._storage_item_repo.get_path(
                id=id, owner_id=owner_id
            )
            if parent_path is None:
                raise FolderNotFoundError()
        else:
            parent_path = ROOT_PATH

        return parent_path

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

    async def upload_file(
        self,
        filename: str,
        parent_id: uuid.UUID | None,
        content: bytes,
        size: int,
        owner: User,
    ) -> FileDTO:
        parent_path = await self._get_base_path(id=parent_id, owner_id=owner.id)

        await self._check_name_not_exists_in_parent(
            name=filename, parent_id=parent_id, owner_id=owner.id
        )

        file_id = uuid.uuid4()
        s3_key = f"{self._s3_files_prefix}/{owner.id}/{file_id}"

        # TODO: все время как скачивается файл, уже удерживается БД соединение.
        await self._s3_adapter.upload(key=s3_key, content=content)

        try:
            file = self._storage_item_repo.add(
                File(
                    id=file_id,
                    name=filename,
                    owner_id=owner.id,
                    parent_id=parent_id,
                    size=size,
                    s3_key=s3_key,
                )
            )

            await self._session.commit()

            path = posixpath.join(parent_path, file.name)

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

        path = await self._storage_item_repo.get_path(
            id=file.id, owner_id=file.owner_id
        )
        if path is None:
            raise FileNotFoundError()

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
        parent_path = await self._get_base_path(id=parent_id, owner_id=owner.id)

        id = uuid.uuid4()
        try:
            folder = self._storage_item_repo.add(
                Folder(id=id, name=name, owner_id=owner.id, parent_id=parent_id)
            )

            await self._session.commit()

            path = posixpath.join(parent_path, folder.name)

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

        path = await self._storage_item_repo.get_path(
            id=folder.id, owner_id=folder.owner_id
        )
        if path is None:
            raise FolderNotFoundError()

        return self._map_folder_to_dto(folder=folder, path=path)

    async def delete_folder(self, id: uuid.UUID, owner: User) -> None:
        folder = await self._fetch_folder(id=id, owner_id=owner.id)

        s3_keys = await self._storage_item_repo.get_s3_key_for_all_children(
            id=id, owner_id=owner.id
        )

        await self._storage_item_repo.delete(folder)
        await self._session.commit()

        await self._s3_adapter.delete_objects(s3_keys)

    async def get_folder_items(
        self, id: uuid.UUID | None, owner: User
    ) -> list[FileDTO | FolderDTO]:
        base_path = await self._get_base_path(id=id, owner_id=owner.id)

        items = await self._storage_item_repo.find_by_parent_and_owner(
            owner_id=owner.id, parent_id=id
        )

        result: list[FileDTO | FolderDTO] = []
        for item in items:
            path = posixpath.join(base_path, item.name)
            result.append(self._map_to_dto(item=item, path=path))

        return result

    async def get_root_items(self, owner: User) -> list[FileDTO | FolderDTO]:
        return await self.get_folder_items(id=None, owner=owner)

    async def search(self, query: str, owner: User) -> list[FileDTO | FolderDTO]:
        results = await self._storage_item_repo.find_by_name_with_path(
            name_substring=query, owner_id=owner.id
        )

        return [
            self._map_to_dto(item=result.item, path=result.path) for result in results
        ]

    async def rename_file(self, id: uuid.UUID, new_name: str, owner: User) -> FileDTO:
        file = await self._fetch_file(id=id, owner_id=owner.id)

        try:
            file.name = new_name
            await self._session.commit()
        except IntegrityError as e:
            await self._session.rollback()
            if UNIQUE_NAME_WITHIN_PARENT in str(e.orig):
                raise NameAlreadyTakenError() from e
            raise

        path = await self._storage_item_repo.get_path(id=file.id, owner_id=owner.id)
        if path is None:
            raise FileNotFoundError()

        return self._map_file_to_dto(file=file, path=path)

    async def move_file(
        self, id: uuid.UUID, new_parent_id: uuid.UUID | None, owner: User
    ) -> FileDTO:
        file = await self._fetch_file(id=id, owner_id=owner.id)

        new_parent_path = await self._get_base_path(id=new_parent_id, owner_id=owner.id)

        try:
            file.parent_id = new_parent_id
            await self._session.commit()
        except IntegrityError as e:
            await self._session.rollback()
            if UNIQUE_NAME_WITHIN_PARENT in str(e.orig):
                raise NameAlreadyTakenError() from e
            raise

        path = posixpath.join(new_parent_path, file.name)

        return self._map_file_to_dto(file=file, path=path)

    async def rename_folder(
        self, id: uuid.UUID, new_name: str, owner: User
    ) -> FolderDTO:
        folder = await self._fetch_folder(id=id, owner_id=owner.id)

        try:
            folder.name = new_name
            await self._session.commit()
        except IntegrityError as e:
            await self._session.rollback()
            if UNIQUE_NAME_WITHIN_PARENT in str(e.orig):
                raise NameAlreadyTakenError() from e
            raise

        path = await self._storage_item_repo.get_path(
            id=folder.id, owner_id=folder.owner_id
        )
        if path is None:
            raise FolderNotFoundError()

        return self._map_folder_to_dto(folder=folder, path=path)

    async def move_folder(
        self, id: uuid.UUID, new_parent_id: uuid.UUID | None, owner: User
    ) -> FolderDTO:
        if id == new_parent_id:
            raise FolderTargetIsSelf()

        folder = await self._fetch_folder(id=id, owner_id=owner.id)

        new_parent_path = await self._get_base_path(id=new_parent_id, owner_id=owner.id)
        if new_parent_id is not None:
            await self._check_target_is_not_subfolder(
                id=id, new_parent_id=new_parent_id, owner_id=folder.owner_id
            )

        try:
            folder.parent_id = new_parent_id
            await self._session.commit()
        except IntegrityError as e:
            await self._session.rollback()
            if UNIQUE_NAME_WITHIN_PARENT in str(e.orig):
                raise NameAlreadyTakenError() from e
            raise

        path = posixpath.join(new_parent_path, folder.name)

        return self._map_folder_to_dto(folder=folder, path=path)

    async def download_folder(self, id: uuid.UUID, owner: User) -> DownloadFolderDTO:
        folder = await self._fetch_folder(id=id, owner_id=owner.id)
        folder_items = await self._storage_item_repo.get_subtree(
            id=folder.id, owner_id=folder.owner_id
        )

        folder_size = sum(item.size for item in folder_items if item.size is not None)
        if folder_size > settings.folder_download_limit:
            raise FolderTooLargeToDownloadError()

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in folder_items:
                s3_key = item.s3_key
                relative_path = item.relative_path

                if s3_key is not None:
                    content = await self._s3_adapter.download(s3_key)
                else:
                    content = b""

                zf.writestr(relative_path, content)

        return DownloadFolderDTO(
            archive_name=f"{folder.name}.zip", content=buffer.getvalue()
        )
