import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.storage.types import StorageItemKind


class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    parent_id: uuid.UUID | None
    size: int

    kind: Literal[StorageItemKind.FILE]

    path: str


class FolderCreate(BaseModel):
    name: str
    parent_id: uuid.UUID | None


class FolderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    parent_id: uuid.UUID | None

    kind: Literal[StorageItemKind.FOLDER]

    path: str


ItemRead = Annotated[FileRead | FolderRead, Field(discriminator="kind")]
