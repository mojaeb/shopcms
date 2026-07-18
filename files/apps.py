from django.apps import AppConfig


class FilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "files"
    verbose_name = "فایل‌ها"

    def ready(self):
        import files.storage.drivers  # noqa: F401
