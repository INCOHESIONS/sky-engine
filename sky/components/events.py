from typing import Callable, Self
from collections.abc import Iterator

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

    def __contains__(self, event: PygameEvent | int) -> bool:
        return self.has(event)

    def __imatmul__(self, event: PygameEvent | int) -> Self:
        self.post(event)
        return self

    @property
    def events(self) -> list[PygameEvent]:
        """The list of events collected this frame."""

        return self._events.copy()

    def handle_events(self) -> Self:
        """
        Handles all events in the event queue. Called before `app.pre_update`.

        Returns
        -------
        `Self`
            The events, for chaining.
        """

        self._events = pygame.event.get()

        for event in self:
            self.on_event.notify(event)

        return self

    def any(self, /, *args: int) -> bool:
        """
        Checks if any of the specified events are in the event queue.

        Parameters
        ----------
        *args: `int`
            The types of events to check for.

        Returns
        -------
        `bool`
            Whether any of the specified events are in the event queue.
        """

        return any(self.has(type) for type in args)

    def all(self, /, *args: int) -> bool:
        """
        Checks if all of the specified events are in the event queue.

        Parameters
        ----------
        *args: `int`
            The types of events to check for.

        Returns
        -------
        `bool`
            Whether all of the specified events are in the event queue.
        """

        return all(self.has(type) for type in args)

    def has(self, type: PygameEvent | int, /) -> bool:
        """
        Checks if an event of a certain type is in the event queue.

        Parameters
        ----------
        type: `int`
            The type of event to check for.

        Returns
        -------
        `bool`
            Whether an event of the specified type is in the event queue.
        """

        return self.get(type if isinstance(type, int) else type.type) is not None

    def lacks(self, type: PygameEvent | int, /) -> bool:
        """
        Checks if an event of a certain type is not in the event queue.

        Parameters
        ----------
        type: `pygame.event.Event | int`
            The type of event to check for.

        Returns
        -------
        `bool`
            Whether an event of the specified type is not in the event queue.
        """

        return not self.has(type)

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

        return first(self.get_many(type))

    def get_many(self, type: int, /) -> list[PygameEvent]:
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
