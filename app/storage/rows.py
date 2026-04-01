from typing import NamedTuple

from app.storage.models import StorageItem


class SubtreeNodeRow(NamedTuple):
    relative_path: str
    s3_key: str | None


class StorageItemWithPathRow(NamedTuple):
    item: StorageItem
    path: str
