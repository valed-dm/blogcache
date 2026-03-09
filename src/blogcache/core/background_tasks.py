"""Registry for fire-and-forget background tasks so they can be awaited on shutdown."""

import asyncio
from typing import Any


_pending_tasks: list[asyncio.Task[Any]] = []


def register(task: asyncio.Task[Any]) -> None:
    """Register a background task so it can be awaited during app shutdown."""
    _pending_tasks.append(task)


def get_pending() -> list[asyncio.Task[Any]]:
    """Return a snapshot of currently pending tasks."""
    return list(_pending_tasks)


async def wait_all() -> None:
    """Wait for all registered tasks to complete (e.g. on shutdown).
    Ignores exceptions."""
    pending = get_pending()
    if not pending:
        return
    await asyncio.gather(*pending, return_exceptions=True)
