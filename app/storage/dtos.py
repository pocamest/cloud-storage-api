import uuid
from dataclasses import dataclass
from typing import Literal

from app.storage.types import StorageItemKind


@dataclass
class FileDTO:
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    parent_id: uuid.UUID | None
    size: int
    path: str

    kind: Literal[StorageItemKind.FILE] = StorageItemKind.FILE


@dataclass
class FolderDTO:
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    parent_id: uuid.UUID | None
    path: str

    kind: Literal[StorageItemKind.FOLDER] = StorageItemKind.FOLDER


@dataclass
class DownloadFileDTO:
    filename: str
    content: bytes


@dataclass
class DownloadFolderDTO:
    archive_name: str
    content: bytes
