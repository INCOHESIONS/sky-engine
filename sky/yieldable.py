"""Contains `Yieldable`s, values that can halt the execution of a `Coroutine` for a period of time."""

# pyright: reportUninitializedInstanceVariable=false

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, Callable, ClassVar, final, override

if TYPE_CHECKING:
    from .app import App

__all__ = [
    "WaitForFrames",
    "WaitForSeconds",
    "WaitUntil",
    "WaitWhile",
    "Yieldable",
]


class Yieldable(ABC):
    """Base class for `Yieldable`s: values that tell the `Executor` to wait or continue executing a `Coroutine`."""

    app: ClassVar[App]

    @abstractmethod
    def is_ready(self) -> bool:
        raise NotImplementedError()


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
    def is_ready(self) -> bool:
        return self.app.chrono.frames - self._frames_started >= self.frames


@final
@dataclass
class WaitForSeconds(Yieldable):
    """Waits for a certain amount of seconds to pass."""

    seconds: float

    def __post_init__(self) -> None:
        self._time_started = perf_counter()

    @override
    def is_ready(self) -> bool:
        return perf_counter() - self._time_started >= self.seconds


@final
@dataclass
class WaitWhile(Yieldable):
    """Waits while a certain condition is not met."""

    func: Callable[[], bool]

    @override
    def is_ready(self) -> bool:
        return not self.func()


@final
@dataclass
class WaitUntil(Yieldable):
    """Waits until a certain condition is met."""

    func: Callable[[], bool]

    @override
    def is_ready(self) -> bool:
        return self.func()
