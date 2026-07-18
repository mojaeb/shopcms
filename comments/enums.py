"""Comment enumerations."""

from django.db import models


class CommentStatus(models.TextChoices):
    PENDING = "pending", "در انتظار تایید"
    APPROVED = "approved", "تایید شده"
    REJECTED = "rejected", "رد شده"
