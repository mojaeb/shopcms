"""Storage driver base classes."""

from abc import ABC, abstractmethod

from django.core.files.base import ContentFile


class StorageDriverBase(ABC):
    codename: str = ""
    label: str = ""

    @abstractmethod
    def save(self, path: str, content: ContentFile) -> str:
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        pass

    @abstractmethod
    def url(self, path: str) -> str:
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    def validate_config(self, config: dict) -> None:
        return None
