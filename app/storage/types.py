from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, TypeVar

from fastapi import UploadFile
from pydantic import AfterValidator, StringConstraints, TypeAdapter

from app.core.config import settings
from app.storage.constants import (
    STORAGE_ITEM_NAME_MAX_LENGTH,
    STORAGE_ITEM_NAME_PATTERN,
)
from app.storage.exceptions import FileTooLargeError

if TYPE_CHECKING:
    from app.storage.models import StorageItem


class StorageItemKind(StrEnum):
    FILE = "file"
    FOLDER = "folder"


StorageItemName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        max_length=STORAGE_ITEM_NAME_MAX_LENGTH,
        pattern=STORAGE_ITEM_NAME_PATTERN,
    ),
]

filename_adapter = TypeAdapter(StorageItemName)


def validate_file_by_name(file: UploadFile) -> UploadFile:
    filename = file.filename
    if filename is None:
        raise ValueError("Filename is required")
    filename_adapter.validate_python(filename)
    return file


def validate_file_by_size(file: UploadFile) -> UploadFile:
    size = file.size
    if size is None:
        raise ValueError("File size cannot be None")
    if size > settings.file_size_limit:
        raise FileTooLargeError()
    return file


ValidUploadFile = Annotated[
    UploadFile,
    AfterValidator(validate_file_by_name),
    AfterValidator(validate_file_by_size),
]

StorageItemT = TypeVar("StorageItemT", bound="StorageItem")
