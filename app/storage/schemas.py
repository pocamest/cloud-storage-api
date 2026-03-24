import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.storage.types import StorageItemKind, StorageItemName


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
    name: StorageItemName
    parent_id: uuid.UUID | None


class FolderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    parent_id: uuid.UUID | None

    kind: Literal[StorageItemKind.FOLDER]

    path: str


StorageItemRead = Annotated[FileRead | FolderRead, Field(discriminator="kind")]


class FileRename(BaseModel):
    new_name: StorageItemName


class FileMove(BaseModel):
    new_parent_id: uuid.UUID | None


class FolderRename(BaseModel):
    new_name: StorageItemName


class FolderMove(BaseModel):
    new_parent_id: uuid.UUID | None
