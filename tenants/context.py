"""Current store context using contextvars."""

from contextvars import ContextVar
from typing import Optional

from tenants.models import Store

_current_store: ContextVar[Optional[Store]] = ContextVar("current_store", default=None)


def set_current_store(store: Optional[Store]) -> None:
    _current_store.set(store)


def get_current_store() -> Optional[Store]:
    return _current_store.get()


def clear_current_store() -> None:
    _current_store.set(None)
