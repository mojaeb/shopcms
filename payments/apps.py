from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payments"
    verbose_name = "پرداخت"

    def ready(self):
        # Load provider modules so @register gateways (including Zarinpal) are available.
        import payments.providers  # noqa: F401
