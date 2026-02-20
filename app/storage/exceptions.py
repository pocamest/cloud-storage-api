from fastapi import status

from app.core.exceptions import AppError, ErrorCode


class StorageError(AppError):
    pass


class FolderNotFoundError(StorageError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Folder not found"
    error_code = ErrorCode.FOLDER_NOT_FOUND


class ParentIsNotFolderError(StorageError):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Parent is not a folder"
    error_code = ErrorCode.PARENT_IS_NOT_FOLDER


class NameAlreadyTakenError(StorageError):
    status_code = status.HTTP_409_CONFLICT
    detail = "The name is already taken"
    error_code = ErrorCode.NAME_ALREADY_TAKEN
