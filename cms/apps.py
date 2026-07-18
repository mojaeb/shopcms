from django.apps import AppConfig


class CmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cms"
    verbose_name = "مدیریت محتوا"

    def ready(self):
        import cms.signals  # noqa: F401
