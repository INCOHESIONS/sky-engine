from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, Callable, override

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


class Yieldable(ABC):
    app: App

    @abstractmethod
    def ready(self) -> bool: ...


@dataclass
class WaitForFrames(Yieldable):
    frames: int

    def __post_init__(self) -> None:
        self._frames_started = self.app.chrono.frames

    @override
    def ready(self) -> bool:
        return self.app.chrono.frames - self._frames_started >= self.frames


@dataclass
class WaitForSeconds(Yieldable):
    seconds: float

    def __post_init__(self) -> None:
        self._time_started = perf_counter()

    @override
    def ready(self) -> bool:
        return perf_counter() - self._time_started >= self.seconds


@dataclass
class WaitWhile(Yieldable):
    func: Callable[[], bool]

    @override
    def ready(self) -> bool:
        return self.func()


@dataclass
class WaitUntil(Yieldable):
    func: Callable[[], bool]

    @override
    def ready(self) -> bool:
        return not self.func()


def singleton[T: type](cls: T) -> T:
    """Makes the decorated class a singleton while keeping its type."""
    return untyped_singleton(cls)  # type: ignore
