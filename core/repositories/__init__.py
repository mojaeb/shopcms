"""Base repository pattern for data access layer."""

from typing import Generic, Optional, TypeVar

from django.db import models

ModelType = TypeVar("ModelType", bound=models.Model)


class BaseRepository(Generic[ModelType]):
    """Generic repository for CRUD operations."""

    model: type[ModelType]

    def __init__(self, model: type[ModelType] | None = None):
        if model is not None:
            self.model = model

    def get_by_id(self, pk: int) -> Optional[ModelType]:
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def get_all(self):
        return self.model.objects.all()

    def create(self, **kwargs) -> ModelType:
        return self.model.objects.create(**kwargs)

    def update(self, instance: ModelType, **kwargs) -> ModelType:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance: ModelType) -> None:
        instance.delete()

    def filter(self, **kwargs):
        return self.model.objects.filter(**kwargs)
