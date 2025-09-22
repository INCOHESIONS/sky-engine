from typing import Callable, Iterator

import pygame
from pygame.event import Event as PygameEvent

from ..core import Component
from ..listenable import Listenable
from ..utils import filter_by_attrs, first

__all__ = ["Events"]


type _EventListener = Callable[[PygameEvent], None]


class Events(Component):
    """Handles pygame events."""

    def __init__(self) -> None:
        self._events: list[PygameEvent] = []
        self.on_event = Listenable[_EventListener]()

    def __iter__(self) -> Iterator[PygameEvent]:
        return iter(self._events)

    @property
    def events(self) -> list[PygameEvent]:
        """The list of events collected this frame."""

        return self._events.copy()

    def handle_events(self) -> None:
        """Handles all events in the event queue. Called before `app.pre_update`."""

        self._events = pygame.event.get()

        for event in self:
            self.on_event.notify(event)

    def get(self, type: int, /) -> PygameEvent | None:
        """
        Gets an event of a certain type.

        Parameters
        ----------
        type: `int`
            The type of event to get.

        Returns
        -------
        `pygame.event.Event | None`
            The event of the specified type, or None if no event of that type was found.
        """

        return first(self.get_all(type))

    def get_all(self, type: int, /) -> list[PygameEvent]:
        """
        Gets all events of a certain type.

        Parameters
        ----------
        type: `int`
            The type of event to get.

        Returns
        -------
        `list[pygame.event.Event]`
            The events of the specified type.
        """

        return list(filter_by_attrs(self._events, type=type))

    def post(self, event: PygameEvent | int, /) -> None:
        """
        Posts an event to the event queue to be handled next frame.

        Parameters
        ----------
        event: `pygame.event.Event | int`
            The event to post.
        """

        pygame.event.post(PygameEvent(event) if isinstance(event, int) else event)

    def cancel(self, event: PygameEvent | int, /) -> None:
        """
        Removes an event from the event queue.

        Parameters
        ----------
        event: `pygame.event.Event | int`
            The event to remove.
        """

        pygame.event.clear(type := event if isinstance(event, int) else event.type)

        for event in filter_by_attrs(self, type=type):
            self._events.remove(event)
