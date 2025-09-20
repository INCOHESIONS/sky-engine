from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, Callable, final, override

from singleton_decorator import singleton as untyped_singleton  # type: ignore

if TYPE_CHECKING:
    from .app import App

__all__ = [
    "Component",
    "singleton",
    "WaitForFrames",
    "WaitForSeconds",
    "WaitUntil",
    "WaitWhile",
    "Yieldable",
]


class Component:
    """Base class for components."""

    app: App

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def update(self) -> None: ...


class Yieldable(ABC):
    """Base class for yieldables: values that tell the coroutine executor to wait or continue executing a coroutine."""

    app: App

    @abstractmethod
    def ready(self) -> bool: ...


@final
@dataclass
class WaitForFrames(Yieldable):
    """
    Waits for a certain amount of frames to pass. By default, it waits for 1 frame.
    If None is returned from a coroutine, it will also wait for 1 frame.
    """

    frames: int = 1

    def __post_init__(self) -> None:
        self._frames_started = self.app.chrono.frames

    @override
    def ready(self) -> bool:
        return self.app.chrono.frames - self._frames_started >= self.frames


@final
@dataclass
class WaitForSeconds(Yieldable):
    """Waits for a certain amount of seconds to pass."""

    seconds: float

    def __post_init__(self) -> None:
        self._time_started = perf_counter()

    @override
    def ready(self) -> bool:
        return perf_counter() - self._time_started >= self.seconds


@final
@dataclass
class WaitWhile(Yieldable):
    """Waits while a certain condition is not met."""

    func: Callable[[], bool]

    @override
    def ready(self) -> bool:
        return not self.func()


@final
@dataclass
class WaitUntil(Yieldable):
    """Waits until a certain condition is met."""

    func: Callable[[], bool]

    @override
    def ready(self) -> bool:
        return self.func()


def singleton[T: type](cls: T) -> T:
    """Makes the decorated class a singleton while keeping its type."""

    return untyped_singleton(cls)  # type: ignore
