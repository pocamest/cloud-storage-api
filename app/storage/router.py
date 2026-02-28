import uuid
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Form, UploadFile, status
from fastapi.responses import Response

from app.auth.dependencies import CurrentUserDep
from app.storage.dependencies import StorageServiceDep
from app.storage.models import File, Folder
from app.storage.schemas import FileRead, FolderCreate, FolderRead

router = APIRouter(tags=["storage"])


# TODO: пока загружаю весь файл, возможно переделаю на стриминг
@router.post(
    "/files/upload", response_model=FileRead, status_code=status.HTTP_201_CREATED
)
async def upload_file(
    file: UploadFile,
    storage_service: StorageServiceDep,
    user: CurrentUserDep,
    parent_id: Annotated[uuid.UUID | None, Form()] = None,
) -> File:
    content = await file.read()
    return await storage_service.upload_file(
        filename=file.filename, parent_id=parent_id, content=content, owner=user
    )


@router.get("/files/{file_id}", response_model=FileRead)
async def get_file(
    file_id: uuid.UUID, storage_service: StorageServiceDep, user: CurrentUserDep
) -> File:
    return await storage_service.get_file(id=file_id, owner=user)


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID, storage_service: StorageServiceDep, user: CurrentUserDep
) -> None:
    await storage_service.delete_file(id=file_id, owner=user)


# TODO: потом переделам на стриминг
@router.get("/files/{file_id}/download")
async def download_file(
    file_id: uuid.UUID, storage_service: StorageServiceDep, user: CurrentUserDep
) -> Response:
    data = await storage_service.download_file(id=file_id, owner=user)
    encode_filename = quote(data.filename)

    # TODO: потом спрятать
    return Response(
        data.content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encode_filename}"
        },
    )


@router.post("/folders", response_model=FolderRead, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_data: FolderCreate, storage_service: StorageServiceDep, user: CurrentUserDep
) -> Folder:
    return await storage_service.create_folder(
        name=folder_data.name, parent_id=folder_data.parent_id, owner=user
    )
