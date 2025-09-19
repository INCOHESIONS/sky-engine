from __future__ import annotations

from typing import Any, Callable, Iterator, Self

__all__ = ["Listenable"]


# Not simply called event to differentiate from pygame.event.Event
class Listenable[TListener: Callable[..., Any] = Callable[[], None]]:
    def __init__(self, cancellable: bool = False, once: bool = False) -> None:
        self._listeners: list[TListener] = []
        self._cancellable = cancellable
        self._once = once
        self._called = False

    def __iter__(self) -> Iterator[TListener]:
        return iter(self._listeners)

    def __call__(self, listener: TListener) -> Self:
        self.add(listener)
        return self

    def __iadd__(self, listener: TListener) -> Self:
        self.add(listener)
        return self

    def __isub__(self, listener: TListener) -> Self:
        self.remove(listener)
        return self

    def add(self, listener: TListener, /) -> None:
        self._listeners.append(listener)

    def remove(self, listener: TListener, /) -> None:
        self._listeners.remove(listener)

    def clear(self) -> None:
        self._listeners.clear()

    def notify(self, *args: Any, **kwargs: Any) -> None:
        if self._once and self._called:
            return

        for listener in self._listeners:
            if listener(*args, **kwargs) and self._cancellable:
                break

        self._called = True
