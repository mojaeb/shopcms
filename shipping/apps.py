from django.apps import AppConfig


class ShippingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shipping"
    verbose_name = "ارسال"

    def ready(self):
        from shipping.providers import registry  # noqa: F401
