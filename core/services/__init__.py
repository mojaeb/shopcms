"""Base service layer for business logic."""

from typing import Generic, TypeVar

ModelType = TypeVar("ModelType")


class BaseService(Generic[ModelType]):
    """Base service class - all business logic should live in services."""

    def __init__(self, repository=None):
        self.repository = repository
