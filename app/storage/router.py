import uuid
from typing import Annotated

from fastapi import APIRouter, Form, UploadFile, status

from app.auth.dependencies import CurrentUserDep
from app.storage.dependencies import StorageServiceDep
from app.storage.models import File
from app.storage.schemas import FileRead

router = APIRouter(prefix="/files", tags=["files"])


# TODO: пока загружаю весь файл, возможно переделаю на стриминг
@router.post("/upload", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile,
    storage_service: StorageServiceDep,
    user: CurrentUserDep,
    parent_id: Annotated[uuid.UUID | None, Form()] = None,
) -> File:
    content = await file.read()
    return await storage_service.upload_file(
        filename=file.filename, parent_id=parent_id, content=content, user=user
    )


@router.get("/{file_id}", response_model=FileRead)
async def get_file(
    file_id: uuid.UUID, storage_service: StorageServiceDep, user: CurrentUserDep
) -> File:
    return await storage_service.get_file(id=file_id, owner=user)
