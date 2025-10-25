"""Contains the `Windowing` component that handles windowing and display management."""

from __future__ import annotations

from typing import final, override

import pygame
from screeninfo import get_monitors

from ..core import Component, Monitor
from ..spec import WindowSpec
from ..utils import filter_by_attrs, first, get_by_attrs
from ..window import Window

__all__ = ["Windowing"]


@final
class Windowing(Component):
    """Handles windowing."""

    WINDOWFULLSCREENED = pygame.USEREVENT + 1

    def __init__(self) -> None:
        Window.app = self.app
        Window.windowing = self

        self._windows: list[Window] = []

        self._monitors = [
            Monitor.from_monitor(monitor, index=i)
            for i, monitor in enumerate(get_monitors())
        ]

        if self.spec and self.spec.initialization == "immediate":
            self._initialize()

    @property
    def main_window(self) -> Window | None:
        """
        The main window, or `None` if the app is headless.\n
        Use `app.window` for a version of this property that can't be `None`.
        """

        return self._windows[0]

    @property
    def extra_windows(self) -> list[Window]:
        """All extra windows."""

        return self._windows[1:]

    @property
    def windows(self) -> list[Window]:
        """All windows, both main and extra."""

        return self._windows.copy()

    @property
    def spec(self) -> WindowSpec | None:
        """The window spec, or `None` if the app is headless."""

        return self.app.spec.window_spec

    @property
    def monitors(self) -> list[Monitor]:
        """Information about all connected monitors."""

        return self._monitors

    @property
    def primary_monitor(self) -> Monitor:
        """Information about the primary monitor."""

        return first(
            filter_by_attrs(self._monitors, is_primary=True), default=self.monitors[0]
        )

    main_monitor = primary_monitor  # alias

    @override
    def start(self) -> None:
        if self.spec and self.spec.initialization == "deferred":
            self._initialize()

    @override
    def update(self) -> None:
        for window in self.windows:
            window.on_render.notify()

    @override
    def stop(self) -> None:
        for window in self.windows:
            window.destroy()

    def add_extra(self, /, *, spec: WindowSpec) -> Window:
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

        self._windows.append(wrapper := Window(spec=spec))
        return wrapper

    def remove_extra(self, window: Window | pygame.Window, /) -> None:
        """
        Removes and destroys the specified extra window.\n
        Finds a window using its `underlying` property if a `pygame.Window` is passed.

        Parameters
        ----------
        window: `WindowWrapper | pygame.Window`
            The window to remove.

        Raises
        ------
        `ValueError`
            If the window wasn't found.
        """

        win = (
            get_by_attrs(self._windows, _underlying=window)
            if isinstance(window, pygame.Window)
            else window
        )

        if win is None:
            raise ValueError(f"Window {window.title} not found.")

        if win is self.main_window:
            raise ValueError("Cannot remove main window.")

        self._windows.remove(win)
        win.destroy()

    def clear_extras(self) -> None:
        """Removes all extra windows."""

        for window in self.extra_windows:
            self.remove_extra(window)

    def _initialize(self) -> None:
        assert self.spec

        self._windows.append(Window(spec=self.spec))

        self.app.teardown += self.clear_extras

        self.app.events.add_callback(pygame.WINDOWCLOSE, self._handle_close)

    def _handle_close(self, event: pygame.event.Event, /) -> None:
        assert self.main_window

        if event.window == self.main_window.underlying:
            self.app.quit()
        else:
            self.remove_extra(event.window)
