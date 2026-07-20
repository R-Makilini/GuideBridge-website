from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    @abstractmethod
    def upload(self, file_obj: BinaryIO, key: str, content_type: str) -> str:
        """Upload a file and return its publicly accessible (or servable) URL."""

    @abstractmethod
    def delete(self, key: str) -> None:
        ...
