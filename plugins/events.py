"""Event bus for plugin hooks."""

import logging
from collections import defaultdict
from typing import Callable

logger = logging.getLogger(__name__)

_listeners: dict[str, list[Callable]] = defaultdict(list)


def on(event: str):
    """Register an event listener."""

    def decorator(func: Callable):
        _listeners[event].append(func)
        return func

    return decorator


def emit(event: str, **payload) -> list:
    """Dispatch an event to all registered listeners."""
    results = []
    for listener in list(_listeners.get(event, [])):
        try:
            results.append(listener(**payload))
        except Exception:
            logger.exception("Event listener failed for %s", event)
    return results


def clear_listeners(event: str | None = None) -> None:
    """Clear listeners (mainly for tests)."""
    if event:
        _listeners.pop(event, None)
    else:
        _listeners.clear()


def list_events() -> list[str]:
    return sorted(_listeners.keys())
