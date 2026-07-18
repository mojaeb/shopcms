"""Local filesystem storage driver."""

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from files.storage.base import StorageDriverBase
from files.storage.registry import register


@register
class LocalStorageDriver(StorageDriverBase):
    codename = "local"
    label = "Local"

    def save(self, path: str, content: ContentFile) -> str:
        if default_storage.exists(path):
            default_storage.delete(path)
        return default_storage.save(path, content)

    def delete(self, path: str) -> None:
        if default_storage.exists(path):
            default_storage.delete(path)

    def url(self, path: str) -> str:
        return default_storage.url(path)

    def exists(self, path: str) -> bool:
        return default_storage.exists(path)

    def validate_config(self, config: dict) -> None:
        if not getattr(settings, "MEDIA_ROOT", None):
            raise ValueError("MEDIA_ROOT is not configured")
