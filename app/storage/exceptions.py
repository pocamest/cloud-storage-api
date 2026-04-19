from fastapi import status

from app.core.config import settings
from app.core.exceptions import AppError, ErrorCode


class StorageError(AppError):
    pass


class FileNotFoundError(StorageError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "File not found"
    error_code = ErrorCode.FILE_NOT_FOUND


class FileTooLargeError(StorageError):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    detail = (
        f"File is too large, limit size: {settings.file_size_limit.human_readable()}"
    )
    error_code = ErrorCode.FILE_TOO_LARGE


class FolderNotFoundError(StorageError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Folder not found"
    error_code = ErrorCode.FOLDER_NOT_FOUND


class FolderTooLargeToDownloadError(StorageError):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = (
        "Folder is too large to download, "
        f"limit size: {settings.folder_download_limit.human_readable()}"
    )
    error_code = ErrorCode.FOLDER_TOO_LARGE_TO_DOWNLOAD


class FolderTargetIsSelf(StorageError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Folder cannot be moved into self"
    error_code = ErrorCode.FOLDER_TARGET_IS_SELF


class FolderTargetIsSubfolder(StorageError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Folder cannot be moved into subfolder"
    error_code = ErrorCode.FOLDER_TARGET_IS_SUBFOLDER


class NameAlreadyTakenError(StorageError):
    status_code = status.HTTP_409_CONFLICT
    detail = "The name is already taken"
    error_code = ErrorCode.NAME_ALREADY_TAKEN
