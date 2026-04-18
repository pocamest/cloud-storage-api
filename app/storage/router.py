import uuid
from typing import Annotated, cast
from urllib.parse import quote

from fastapi import APIRouter, Form, status
from fastapi.responses import Response

from app.auth.dependencies import CurrentUserDep
from app.storage.dependencies import StorageServiceDep
from app.storage.dtos import FileDTO, FolderDTO
from app.storage.schemas import (
    FileMove,
    FileRead,
    FileRename,
    FolderCreate,
    FolderMove,
    FolderRead,
    FolderRename,
    StorageItemRead,
)
from app.storage.types import StorageItemName, ValidUploadFile


def _build_download_response(content: bytes, filename: str) -> Response:
    encode_filename = quote(filename)
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encode_filename}"
        },
    )


router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/search", response_model=list[StorageItemRead])
async def search(
    query: str, storage_service: StorageServiceDep, user: CurrentUserDep
) -> list[FileDTO | FolderDTO]:
    return await storage_service.search(query=query, owner=user)


# TODO: пока загружаю весь файл, возможно переделаю на стриминг
@router.post(
    "/files/upload", response_model=FileRead, status_code=status.HTTP_201_CREATED
)
async def upload_file(
    file: ValidUploadFile,
    storage_service: StorageServiceDep,
    user: CurrentUserDep,
    parent_id: Annotated[uuid.UUID | None, Form()] = None,
) -> FileDTO:
    filename = cast(StorageItemName, file.filename)
    content = await file.read()
    file_size = len(content)
    return await storage_service.upload_file(
        filename=filename,
        parent_id=parent_id,
        content=content,
        size=file_size,
        owner=user,
    )


@router.get("/files/{file_id}", response_model=FileRead)
async def get_file(
    file_id: uuid.UUID, storage_service: StorageServiceDep, user: CurrentUserDep
) -> FileDTO:
    return await storage_service.get_file(id=file_id, owner=user)


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID, storage_service: StorageServiceDep, user: CurrentUserDep
) -> None:
    await storage_service.delete_file(id=file_id, owner=user)


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: uuid.UUID, storage_service: StorageServiceDep, user: CurrentUserDep
) -> Response:
    data = await storage_service.download_file(id=file_id, owner=user)
    return _build_download_response(content=data.content, filename=data.filename)


@router.post("/files/{file_id}/rename", response_model=FileRead)
async def rename_file(
    file_id: uuid.UUID,
    rename_data: FileRename,
    storage_service: StorageServiceDep,
    user: CurrentUserDep,
) -> FileDTO:
    return await storage_service.rename_file(
        id=file_id, new_name=rename_data.new_name, owner=user
    )


@router.post("/files/{file_id}/move", response_model=FileRead)
async def move_file(
    file_id: uuid.UUID,
    move_data: FileMove,
    storage_service: StorageServiceDep,
    user: CurrentUserDep,
) -> FileDTO:
    return await storage_service.move_file(
        id=file_id, new_parent_id=move_data.new_parent_id, owner=user
    )


@router.post("/folders", response_model=FolderRead, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_data: FolderCreate, storage_service: StorageServiceDep, user: CurrentUserDep
) -> FolderDTO:
    return await storage_service.create_folder(
        name=folder_data.name, parent_id=folder_data.parent_id, owner=user
    )


@router.get("/folders/{folder_id}", response_model=FolderRead)
async def get_folder(
    folder_id: uuid.UUID, storage_service: StorageServiceDep, user: CurrentUserDep
) -> FolderDTO:
    return await storage_service.get_folder(id=folder_id, owner=user)


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: uuid.UUID, storage_service: StorageServiceDep, user: CurrentUserDep
) -> None:
    await storage_service.delete_folder(id=folder_id, owner=user)


@router.get("/folders/{folder_id}/download")
async def download_folder(
    folder_id: uuid.UUID, storage_service: StorageServiceDep, user: CurrentUserDep
) -> Response:
    data = await storage_service.download_folder(id=folder_id, owner=user)

    return _build_download_response(content=data.content, filename=data.archive_name)


@router.get("/folders/root/items", response_model=list[StorageItemRead])
async def get_root_items(
    storage_service: StorageServiceDep, user: CurrentUserDep
) -> list[FileDTO | FolderDTO]:
    return await storage_service.get_root_items(owner=user)


@router.get("/folders/{folder_id}/items", response_model=list[StorageItemRead])
async def get_folder_items(
    folder_id: uuid.UUID, storage_service: StorageServiceDep, user: CurrentUserDep
) -> list[FileDTO | FolderDTO]:
    return await storage_service.get_folder_items(id=folder_id, owner=user)


@router.post("/folders/{folder_id}/rename", response_model=FolderRead)
async def rename_folder(
    folder_id: uuid.UUID,
    rename_data: FolderRename,
    storage_service: StorageServiceDep,
    user: CurrentUserDep,
) -> FolderDTO:
    return await storage_service.rename_folder(
        id=folder_id, new_name=rename_data.new_name, owner=user
    )


@router.post("/folders/{folder_id}/move", response_model=FolderRead)
async def move_folder(
    folder_id: uuid.UUID,
    move_data: FolderMove,
    storage_service: StorageServiceDep,
    user: CurrentUserDep,
) -> FolderDTO:
    return await storage_service.move_folder(
        id=folder_id, new_parent_id=move_data.new_parent_id, owner=user
    )
