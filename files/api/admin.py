"""Store admin files API."""

from ninja import File, Form, Router, Schema, UploadedFile
from ninja.errors import HttpError
from ninja.pagination import PageNumberPagination, paginate

from dashboard.authentication_store import store_files_auth
from files.services.file import FileError, FileService
from tenants.context import get_current_store

router = Router(auth=store_files_auth)
service = FileService()


class FileUpdateSchema(Schema):
    title: str | None = None
    alt_text: str | None = None
    folder: str | None = None
    is_public: bool | None = None


class FileListSchema(Schema):
    id: int
    file_type: str
    original_name: str
    url: str
    mime_type: str
    size_bytes: int
    width: int | None = None
    height: int | None = None
    folder: str
    title: str
    alt_text: str
    is_public: bool
    storage_driver: str
    created_at: str
    thumbnails: list


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/drivers")
def list_storage_drivers(request):
    return service.storage_manager.list_available_drivers()


@router.get("", response=list[FileListSchema])
@paginate(PageNumberPagination, page_size=24)
def list_files(request, file_type: str | None = None, folder: str = ""):
    store = _store(request)
    files = service.list_files(store, file_type=file_type, folder=folder)
    return [service.serialize_file(f) for f in files]


@router.post("/upload")
def upload_file(
    request,
    file: UploadedFile = File(...),
    folder: str = Form(""),
    title: str = Form(""),
    alt_text: str = Form(""),
    is_public: bool = Form(True),
):
    store = _store(request)
    user = getattr(request, "auth", None)
    try:
        media = service.upload(
            store,
            file,
            user=user,
            folder=folder,
            title=title,
            alt_text=alt_text,
            is_public=is_public,
        )
        return service.serialize_file(media)
    except FileError as exc:
        raise HttpError(400, str(exc))


@router.get("/{file_id}")
def get_file(request, file_id: int):
    store = _store(request)
    try:
        media = service.get_file(store, file_id)
        return service.serialize_file(media)
    except FileError as exc:
        raise HttpError(404, str(exc))


@router.put("/{file_id}")
def update_file(request, file_id: int, payload: FileUpdateSchema):
    store = _store(request)
    try:
        media = service.get_file(store, file_id)
    except FileError as exc:
        raise HttpError(404, str(exc))

    data = {k: v for k, v in payload.dict().items() if v is not None}
    if "folder" in data:
        data["folder"] = service._sanitize_folder(data["folder"])

    for key, value in data.items():
        setattr(media, key, value)
    media.save()
    return service.serialize_file(media)


@router.delete("/{file_id}")
def delete_file(request, file_id: int):
    store = _store(request)
    try:
        service.delete_file(store, file_id)
        return {"success": True}
    except FileError as exc:
        raise HttpError(404, str(exc))
