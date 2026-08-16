from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Core"

    def ready(self):
        # Admin autodiscover runs in django.contrib.admin's AppConfig.ready,
        # which is listed before local apps — registry is complete here.
        from core.admin_scoping import apply_store_admin_scoping

        apply_store_admin_scoping()
