from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, final, override

import pygame
from screeninfo import Monitor, get_monitors

from ..core import Component
from ..spec import WindowSpec
from ..utils import Vector2, get_by_attrs

if TYPE_CHECKING:
    from ..app import App


__all__ = ["Windowing"]


# kind of assuming both pygame and screeninfo use the same indexing system here to match monitors to refresh rates
# i don't have more than one monitor to be able to test this so idk
# pretty ugly but screeninfo doesn't provide refresh rates so it is what it is
@dataclass
class _MonitorInfo:
    name: str
    position: Vector2
    size: Vector2
    is_primary: bool
    index: int

    @classmethod
    def from_monitor(cls, monitor: Monitor, /, *, index: int) -> Self:
        return cls(
            monitor.name or "Unnamed Monitor",
            Vector2(monitor.x, monitor.y),
            Vector2(monitor.width, monitor.height),
            monitor.is_primary or index == 0,
            index,
        )

    @property
    def refresh_rate(self) -> int:
        """The refresh rate of the monitor. Returns -1 if the video system hasn't been initialized."""

        try:
            return pygame.display.get_desktop_refresh_rates()[self.index]
        except pygame.error:
            return -1


@final
class _WindowWrapper:
    app: App

    _magic_fullscreen_position = Vector2(-8, -31)
    _magic_size_offset = Vector2(16, 39)

    def __init__(self, /, *, spec: WindowSpec) -> None:
        self._underlying = pygame.Window(
            spec.title,
            spec.size,
            position=spec.position or (0, 0),
            fullscreen=spec.fullscreen,
            resizable=spec.resizable,
            borderless=spec.borderless,
            opengl=spec.backend == "opengl",
            vulkan=spec.backend == "vulkan",
        )
        self._underlying.get_surface()

        self._spec = spec
        self._fullscreen = spec.fullscreen

        if spec.position is None:
            self.center()

    @property
    def underlying(self) -> pygame.Window:
        """
        The underlying pygame window.\n
        Position, size and fullscreen state should not be modified through this property.
        """

        return self._underlying

    @property
    def surface(self) -> pygame.Surface:
        """The main window's surface."""

        return self._underlying.get_surface()

    @property
    def position(self) -> Vector2:
        """Gets or sets the position of the main window."""

        return Vector2(self._underlying.position)

    @position.setter
    def position(self, value: Vector2) -> None:
        self._underlying.position = value

    @property
    def size(self) -> Vector2:
        """Gets or sets the current size of the main window."""

        return Vector2(self._underlying.size)

    @size.setter
    def size(self, value: Vector2) -> None:
        self._underlying.size = value

    @property
    def fullscreen(self) -> bool:
        """
        Gets or sets the main window's fullscreen state.\n
        Does some extra magic on Windows to get fullscreening to work, unlike `pygame.Window`'s `set_fullscreen` method.
        """

        return self._fullscreen

    @fullscreen.setter
    def fullscreen(self, value: bool) -> None:
        self._fullscreen = value

        if os.name != "nt":
            self._underlying.set_fullscreen(value)

        # this is based on some old code i wrote to fix fullscreening problems with pygame.
        # i don't really know what the magic numbers mean, i just know that they work.
        # well, mostly. at least they do on my machine

        self.size = (
            (self.app.windowing.primary_monitor.size + self._magic_size_offset)
            if value
            else self._spec.size
        )

        self.position = (
            self._magic_fullscreen_position if value else self.centered_position
        )

    @property
    def centered_position(self) -> Vector2:
        """
        The position of the window, centered on the main monitor.

        Returns
        -------
        `Vector2`
            The position of the window.
        """

        return self.app.windowing.primary_monitor.size / 2 - self.size / 2

    def toggle_fullscreen(self) -> None:
        """Toggles fullscreen mode."""

        self.fullscreen = not self._fullscreen

    def center(self) -> None:
        """Centers the window."""
        self.position = self.centered_position

    def destroy(self) -> None:
        """Destroys the window."""
        self._underlying.destroy()

    def flip(self) -> None:
        """Updates the window."""
        self._underlying.flip()

    update = flip


class Windowing(Component):
    """Handles windowing."""

    def __init__(self) -> None:
        _WindowWrapper.app = self.app

        self._main = None
        self._extras: list[_WindowWrapper] = []

        self._monitors = [
            _MonitorInfo.from_monitor(monitor, index=i)
            for i, monitor in enumerate(get_monitors())
        ]

    @property
    def main_window(self) -> _WindowWrapper | None:
        """
        The main window, or `None` if the app is headless.\n
        Use `app.window` for a version of this property that can't be `None`.
        """

        return self._main

    @property
    def spec(self) -> WindowSpec | None:
        """The window spec, or `None` if the app is headless."""

        return self.app.spec.window_spec

    @property
    def monitors(self) -> list[_MonitorInfo]:
        """Information about all connected monitors."""

        return self._monitors

    @property
    def primary_monitor(self) -> _MonitorInfo:
        """Information about the primary monitor."""

        return self._monitors[0]

    @override
    def start(self) -> None:
        if self.spec is None:
            return

        self._main = _WindowWrapper(spec=self.spec)

        self.app.post_update += self._post_update

    @override
    def stop(self) -> None:
        if self._main is not None:
            self._main.destroy()

        for window in self._extras:
            window.destroy()

    def add_extra(self, /, *, spec: WindowSpec) -> _WindowWrapper:
        """
        Creates and adds an extra window from a `WindowSpec`.

        Parameters
        ----------
        spec: `WindowSpec`
            The window spec to create the window from.

        Returns
        -------
        `WindowWrapper`
            The wrapper for the generated window.
        """

        self._extras.append(wrapper := _WindowWrapper(spec=spec))
        return wrapper

    def remove_extra(self, window: _WindowWrapper | pygame.Window, /) -> None:
        """
        Removes and destroys the specified extra window.

        Parameters
        ----------
        window: `WindowWrapper`
            The window to remove.

        Raises
        ------
        `ValueError`
            If the window wasn't found.
        """

        self._extras.remove(
            get_by_attrs(self._extras, _underlying=window)  # type: ignore
            if isinstance(window, pygame.Window)
            else window
        )
        window.destroy()

    def clear_extras(self) -> None:
        """Removes all extra windows."""

        for window in self._extras:
            self.remove_extra(window)

    # uses post_update to guarantee the window is flipped after any user-added components update
    def _post_update(self) -> None:
        self._main.flip()  # type: ignore

        for window in self._extras:
            window.flip()

        if evt := self.app.events.get(pygame.WINDOWCLOSE):
            if evt.window == self._main._underlying:  # type: ignore

                def _cleanup() -> None:
                    self.clear_extras()
                    self.app.quit()

                self.app.teardown += _cleanup
                self.app.quit()
            else:
                self.remove_extra(evt.window)
