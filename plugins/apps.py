from django.apps import AppConfig


class PluginsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "plugins"
    verbose_name = "سیستم افزونه"

    def ready(self):
        from plugins.loader import load_plugins

        load_plugins()
