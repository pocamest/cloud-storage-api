from dataclasses import dataclass


@dataclass
class DownloadFileDTO:
    filename: str
    content: bytes
