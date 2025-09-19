from __future__ import annotations

from typing import TYPE_CHECKING

from singleton_decorator import singleton as untyped_singleton  # type: ignore

if TYPE_CHECKING:
    from .app import App

__all__ = ["Component", "singleton"]


class Component:
    """Base class for components."""

    app: App

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def update(self) -> None: ...


def singleton[T: type](cls: T) -> T:
    """Makes the decorated class a singleton while keeping its type."""
    return untyped_singleton(cls)  # type: ignore
