"""Concrete storage drivers."""

from files.storage.drivers.local import LocalStorageDriver
from files.storage.drivers.remote import MinIOStorageDriver, R2StorageDriver, S3StorageDriver

__all__ = [
    "LocalStorageDriver",
    "S3StorageDriver",
    "MinIOStorageDriver",
    "R2StorageDriver",
]
