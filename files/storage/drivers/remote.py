"""Remote object storage drivers (S3-compatible)."""

from django.core.files.base import ContentFile

from files.storage.base import StorageDriverBase
from files.storage.registry import register


class S3CompatibleDriver(StorageDriverBase):
    required_keys: tuple[str, ...] = ("bucket", "access_key", "secret_key")

    def validate_config(self, config: dict) -> None:
        missing = [key for key in self.required_keys if not config.get(key)]
        if missing:
            raise ValueError(f"Missing storage config keys: {', '.join(missing)}")

    def _not_configured(self) -> RuntimeError:
        return RuntimeError(f"{self.label} driver requires boto3 and store storage settings")

    def save(self, path: str, content: ContentFile) -> str:
        raise self._not_configured()

    def delete(self, path: str) -> None:
        raise self._not_configured()

    def url(self, path: str) -> str:
        raise self._not_configured()

    def exists(self, path: str) -> bool:
        raise self._not_configured()


@register
class S3StorageDriver(S3CompatibleDriver):
    codename = "s3"
    label = "Amazon S3"


@register
class MinIOStorageDriver(S3CompatibleDriver):
    codename = "minio"
    label = "MinIO"
    required_keys = ("bucket", "access_key", "secret_key", "endpoint")


@register
class R2StorageDriver(S3CompatibleDriver):
    codename = "r2"
    label = "Cloudflare R2"
    required_keys = ("bucket", "access_key", "secret_key", "account_id")
