from enum import StrEnum
from typing import Annotated

from fastapi import UploadFile
from pydantic import AfterValidator, StringConstraints, TypeAdapter

from app.storage.constants import (
    STORAGE_ITEM_NAME_MAX_LENGTH,
    STORAGE_ITEM_NAME_PATTERN,
)


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


ValidUploadFile = Annotated[UploadFile, AfterValidator(validate_file_by_name)]
