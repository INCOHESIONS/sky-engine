"""Contains the `Events` component that handles pygame events."""

from collections.abc import Iterator
from typing import Any, Callable, Literal, Self, final

import pygame
from pygame.event import Event as PygameEvent

from ..core import Service
from ..hook import Hook
from ..utils import filter_by_attrs, first

__all__ = ["Events"]


@final
class Events(Service):
    """Handles pygame events."""

    def __init__(self) -> None:
        self._events: list[PygameEvent] = []
        self._callbacks: dict[int, list[Callable[[PygameEvent], None]]] = {}

        self.on_event = Hook[[PygameEvent]]()

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

    def add_callback(
        self, event: PygameEvent | int, callback: Callable[[PygameEvent], Any], /
    ) -> None:
        """
        Adds a callback to be called when the specified event is received.

        Parameters
        ----------
        event : `PygameEvent | int`
            The event to listen for.
        callback : `Callable[[PygameEvent], Any]`
            The callback to call when the event is received.
        """

        type = event.type if isinstance(event, PygameEvent) else event

        def _callback(e: PygameEvent):
            if e.type == type:
                callback(e)

        self._callbacks[type] = self._callbacks.get(type, []) + [_callback]

        self.on_event += _callback

    def remove_callback(self, callback: Callable[[PygameEvent], Any], /) -> None:
        """
        Removes a callback from the event listener.

        Parameters
        ----------
        callback : `Callable[[PygameEvent], Any]`
            The callback to remove.

        Raises
        ------
        ValueError
            If the callback is not registered.
        """

        self.on_event -= callback

    def remove_all_callbacks(self, type: int, /) -> None:
        """
        Removes all callbacks of the specified type from the event listener.

        Parameters
        ----------
        type : `int`
            The type of events to remove callbacks for.

        Raises
        ------
        ValueError
            If the type is not registered.
        """

        # default argument so a ValueError is raised at Hook.__isub__ instead of a KeyError here
        # purely so that the error types from add and remove are consistent
        for callback in self._callbacks.pop(type, []):
            self.on_event -= callback

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

    def post(
        self, event: PygameEvent | int, /, *, attrs: dict[str, Any] | None = None
    ) -> None:
        """
        Posts an event to the event queue to be handled next frame.

        Parameters
        ----------
        event: `pygame.event.Event | int`
            The event to post.
        attrs: `dict[str, Any] | None`, optional
            Additional attributes to add to the event. Only applies if `event` is an `int`.
        """

        pygame.event.post(
            PygameEvent(event, attrs or {}) if isinstance(event, int) else event
        )

    def allow(self, event: PygameEvent | int, /) -> None:
        """
        Allows an event to be posted again, after it was cancelled with the `when` argument being `"always"`.

        Parameters
        ----------
        event: `pygame.event.Event | int`
            The event to allow.
        """

        pygame.event.set_allowed(event if isinstance(event, int) else event.type)

    def cancel(
        self,
        event: PygameEvent | int,
        /,
        *,
        when: Literal["frame", "always"] = "frame",
    ) -> None:
        """
        Removes an event from the event queue.

        Parameters
        ----------
        event: `pygame.event.Event | int`
            The event to remove.
        when: `Literal["frame", "always"]`, optional
            When to cancel the event: only for the current frame or for all subsequent frames. Defaults to "frame".
        """

        pygame.event.clear(type := event if isinstance(event, int) else event.type)

        for event in filter_by_attrs(self, type=type):
            self._events.remove(event)

        if when == "always":
            pygame.event.set_blocked(type)
