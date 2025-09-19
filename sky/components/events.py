from dataclasses import dataclass
from typing import Callable, Final, Iterator, final, override

import pygame
from pygame.event import Event as PygameEvent

from ..core import Component
from ..utils import filter_by_attrs, first

__all__ = ["Events"]


@final
@dataclass
class _Handler:
    type: Final[int]
    func: Final[Callable[[PygameEvent], None]]

    def __call__(self, event: PygameEvent) -> None:
        self.func(event)


class Events(Component):
    def __init__(self) -> None:
        self._events: list[PygameEvent] = []
        self._handlers: list[_Handler] = []

    def __iter__(self) -> Iterator[PygameEvent]:
        return iter(self._events)

    @property
    def events(self) -> list[PygameEvent]:
        return self._events

    @override
    def update(self) -> None:
        for event in self._events:
            map(
                lambda handler: handler(event),
                filter_by_attrs(self._handlers, type=event.type),
            )

    def add_handler(self, type: int, handler: Callable[[PygameEvent], None], /) -> None:
        self._handlers.append(_Handler(type, handler))

    def remove_handler(self, type: int, /) -> None:
        map(self._handlers.remove, filter_by_attrs(self._handlers, type=type))

    def get(self, type: int, /) -> PygameEvent | None:
        return first(self.get_all(type))

    def get_all(self, type: int, /) -> list[PygameEvent]:
        return list(filter_by_attrs(self._events, type=type))

    def post(self, event: PygameEvent | int, /) -> None:
        pygame.event.post(PygameEvent(event) if isinstance(event, int) else event)

    def cancel(self, event: PygameEvent | int, /) -> None:
        pygame.event.clear(type := event if isinstance(event, int) else event.type)
        map(self._events.remove, filter_by_attrs(self._events, type=type))
