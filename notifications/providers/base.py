"""Notification provider base classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SendResult:
    success: bool
    message: str = ""
    external_id: str = ""
    raw: dict | None = None


class NotificationProvider(ABC):
    codename: str = ""
    label: str = ""
    channel_type: str = ""

    @abstractmethod
    def send(self, recipient: str, body: str, config: dict, subject: str = "", metadata: dict | None = None) -> SendResult:
        pass

    def validate_config(self, config: dict) -> None:
        return None
