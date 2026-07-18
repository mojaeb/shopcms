"""Notification enums."""

from django.db import models


class ChannelType(models.TextChoices):
    SMS = "sms", "SMS"
    EMAIL = "email", "Email"
    PUSH = "push", "Push"
    WEBHOOK = "webhook", "Webhook"
    TELEGRAM = "telegram", "Telegram"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
