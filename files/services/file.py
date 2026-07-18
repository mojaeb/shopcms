"""File upload and media management service."""

import logging
import mimetypes
import os
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from PIL import Image

from files.enums import FileType, ThumbnailVariant
from files.models import FileThumbnail, MediaFile
from files.storage.manager import StorageManager

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv", ".zip"}

IMAGE_MIMES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/svg+xml",
}
VIDEO_MIMES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
}


class FileError(Exception):
    pass


class FileService:
    """Upload, thumbnail generation, listing, and deletion."""

    def __init__(self):
        self.storage_manager = StorageManager()

    def detect_file_type(self, filename: str, mime_type: str = "") -> str:
        ext = os.path.splitext(filename)[1].lower()
        mime = mime_type or mimetypes.guess_type(filename)[0] or ""

        if ext in IMAGE_EXTENSIONS or mime in IMAGE_MIMES or mime.startswith("image/"):
            return FileType.IMAGE
        if ext in VIDEO_EXTENSIONS or mime in VIDEO_MIMES or mime.startswith("video/"):
            return FileType.VIDEO
        if ext in DOCUMENT_EXTENSIONS or mime in {"application/pdf", "text/plain"}:
            return FileType.DOCUMENT
        return FileType.OTHER

    def validate_upload(self, uploaded: UploadedFile) -> None:
        max_size = getattr(settings, "FILE_UPLOAD_MAX_SIZE", 10 * 1024 * 1024)
        if uploaded.size > max_size:
            raise FileError(f"حداکثر حجم فایل {max_size // (1024 * 1024)} مگابایت است")

        allowed = getattr(settings, "FILE_ALLOWED_MIME_PREFIXES", ("image/", "video/", "application/pdf"))
        content_type = uploaded.content_type or mimetypes.guess_type(uploaded.name)[0] or ""
        if content_type and not any(content_type.startswith(p) for p in allowed):
            if content_type not in {"text/plain", "text/csv", "application/zip"}:
                raise FileError("نوع فایل مجاز نیست")

    def upload(
        self,
        store,
        uploaded: UploadedFile,
        user=None,
        folder: str = "",
        title: str = "",
        alt_text: str = "",
        is_public: bool = True,
    ) -> MediaFile:
        self.validate_upload(uploaded)
        driver, config = self.storage_manager.get_driver_for_store(store)
        if driver.codename != "local":
            driver.validate_config(config)

        file_type = self.detect_file_type(uploaded.name, uploaded.content_type or "")
        ext = os.path.splitext(uploaded.name)[1].lower() or ""
        safe_folder = self._sanitize_folder(folder)
        filename = f"{uuid.uuid4().hex}{ext}"
        storage_path = self._build_path(store.slug, safe_folder, filename)

        uploaded.seek(0)
        saved_path = driver.save(storage_path, ContentFile(uploaded.read(), name=uploaded.name))
        file_url = self._absolute_url(driver.url(saved_path))

        width = height = None
        if file_type == FileType.IMAGE and ext != ".svg":
            width, height = self._read_image_dimensions(uploaded)

        media = MediaFile.objects.create(
            store=store,
            uploaded_by=user,
            file_type=file_type,
            original_name=uploaded.name,
            storage_path=saved_path,
            storage_driver=driver.codename,
            mime_type=uploaded.content_type or mimetypes.guess_type(uploaded.name)[0] or "",
            size_bytes=uploaded.size,
            width=width,
            height=height,
            url=file_url,
            folder=safe_folder,
            title=title or os.path.splitext(uploaded.name)[0],
            alt_text=alt_text,
            is_public=is_public,
        )

        if file_type == FileType.IMAGE and ext != ".svg":
            self.generate_thumbnails(media, driver)

        return media

    @transaction.atomic
    def generate_thumbnails(self, media: MediaFile, driver=None) -> list[FileThumbnail]:
        if media.file_type != FileType.IMAGE:
            return []

        driver = driver or self.storage_manager.get_driver_for_store(media.store)[0]
        sizes = getattr(settings, "FILE_THUMBNAIL_SIZES", {})
        created = []

        from django.core.files.storage import default_storage

        if not default_storage.exists(media.storage_path):
            return []

        with default_storage.open(media.storage_path, "rb") as source:
            image = Image.open(source)
            image.load()

            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            for variant, dimensions in sizes.items():
                if variant not in ThumbnailVariant.values:
                    continue
                thumb = self._make_thumbnail(image, dimensions)
                buffer = BytesIO()
                thumb.save(buffer, format="JPEG", quality=85, optimize=True)
                buffer.seek(0)

                ext = ".jpg"
                thumb_path = self._build_path(
                    media.store.slug,
                    f"thumbnails/{media.id}",
                    f"{variant}{ext}",
                )
                saved = driver.save(thumb_path, ContentFile(buffer.read(), name=f"{variant}{ext}"))
                thumb_url = self._absolute_url(driver.url(saved))

                obj, _ = FileThumbnail.objects.update_or_create(
                    media_file=media,
                    variant=variant,
                    defaults={
                        "storage_path": saved,
                        "url": thumb_url,
                        "width": thumb.width,
                        "height": thumb.height,
                        "size_bytes": buffer.getbuffer().nbytes,
                    },
                )
                created.append(obj)

        return created

    def list_files(self, store, file_type: str | None = None, folder: str = ""):
        qs = MediaFile.objects.filter(store=store).prefetch_related("thumbnails")
        if file_type:
            qs = qs.filter(file_type=file_type)
        if folder:
            qs = qs.filter(folder=self._sanitize_folder(folder))
        return qs

    def get_file(self, store, file_id: int) -> MediaFile:
        try:
            return MediaFile.objects.prefetch_related("thumbnails").get(store=store, pk=file_id)
        except MediaFile.DoesNotExist as exc:
            raise FileError("فایل یافت نشد") from exc

    @transaction.atomic
    def delete_file(self, store, file_id: int) -> None:
        media = self.get_file(store, file_id)
        driver, _ = self.storage_manager.get_driver_for_store(store)

        for thumb in media.thumbnails.all():
            driver.delete(thumb.storage_path)
        driver.delete(media.storage_path)
        media.delete()

    def serialize_file(self, media: MediaFile, include_thumbnails: bool = True) -> dict:
        data = {
            "id": media.id,
            "file_type": media.file_type,
            "original_name": media.original_name,
            "url": media.url,
            "mime_type": media.mime_type,
            "size_bytes": media.size_bytes,
            "width": media.width,
            "height": media.height,
            "folder": media.folder,
            "title": media.title,
            "alt_text": media.alt_text,
            "is_public": media.is_public,
            "storage_driver": media.storage_driver,
            "created_at": media.created_at.isoformat(),
        }
        if include_thumbnails:
            data["thumbnails"] = [
                {
                    "variant": t.variant,
                    "url": t.url,
                    "width": t.width,
                    "height": t.height,
                    "size_bytes": t.size_bytes,
                }
                for t in media.thumbnails.all()
            ]
        return data

    def _make_thumbnail(self, image: Image.Image, dimensions: tuple[int, int]) -> Image.Image:
        max_w, max_h = dimensions
        copy = image.copy()
        copy.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        return copy

    def _read_image_dimensions(self, uploaded: UploadedFile) -> tuple[int | None, int | None]:
        try:
            uploaded.seek(0)
            with Image.open(uploaded) as img:
                return img.size
        except Exception:
            logger.exception("Failed to read image dimensions")
            return None, None
        finally:
            uploaded.seek(0)

    def _sanitize_folder(self, folder: str) -> str:
        folder = (folder or "").strip().strip("/")
        parts = [p for p in folder.split("/") if p and p not in (".", "..")]
        return "/".join(parts)

    def _build_path(self, store_slug: str, folder: str, filename: str) -> str:
        parts = ["stores", store_slug]
        if folder:
            parts.append(folder)
        parts.append(filename)
        return "/".join(parts)

    def _absolute_url(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        base = getattr(settings, "MEDIA_URL", "/media/")
        if not base.endswith("/"):
            base += "/"
        return f"{base.rstrip('/')}/{url.lstrip('/')}" if not url.startswith("/") else url
