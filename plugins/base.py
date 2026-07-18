"""Plugin base classes and manifest."""

from abc import ABC
from dataclasses import dataclass, field
from typing import Any

from ninja import Router


@dataclass
class PluginSettingField:
    key: str
    label: str
    field_type: str = "string"
    default: Any = None
    required: bool = False
    help_text: str = ""


@dataclass
class PluginManifest:
    codename: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    compatible_store_types: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    settings_schema: list[PluginSettingField] = field(default_factory=list)


class BasePlugin(ABC):
    """Base class for platform plugins."""

    codename: str = ""
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    compatible_store_types: list[str] = []
    provides: list[str] = []

    settings_schema: list[PluginSettingField] = []

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            codename=self.codename,
            name=self.name,
            description=self.description,
            version=self.version,
            compatible_store_types=list(self.compatible_store_types),
            provides=self.get_provides(),
            settings_schema=list(self.settings_schema),
        )

    def get_provides(self) -> list[str]:
        provides = list(self.provides or [])
        if self.get_api_router() and "api" not in provides:
            provides.append("api")
        if self.get_urlpatterns() and "views" not in provides:
            provides.append("views")
        if self.get_template_pages() and "templates" not in provides:
            provides.append("templates")
        if self.settings_schema and "settings" not in provides:
            provides.append("settings")
        return provides

    def default_settings(self) -> dict:
        return {item.key: item.default for item in self.settings_schema}

    def validate_settings(self, settings: dict | None) -> dict:
        data = {**self.default_settings(), **(settings or {})}
        for item in self.settings_schema:
            if item.required and data.get(item.key) in (None, ""):
                raise ValueError(f"Setting '{item.key}' is required")
        return data

    def get_api_router(self) -> Router | None:
        return None

    def get_urlpatterns(self) -> list:
        return []

    def get_admin_classes(self) -> list:
        return []

    def get_template_pages(self) -> dict[str, str]:
        return {}

    def register_events(self) -> None:
        return None
