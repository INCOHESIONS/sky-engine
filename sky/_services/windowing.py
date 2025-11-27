"""Contains the `Windowing` component that handles windowing and display management."""

from __future__ import annotations

from collections.abc import Sequence
from typing import final, override

import pygame
from screeninfo import get_monitors

from ..core import Monitor, Service
from ..spec import WindowSpec
from ..utils import filter_by_attrs, first, get_by_attrs
from ..window import Window

__all__ = ["Windowing"]


@final
class Windowing(Service):
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
    def windows(self) -> Sequence[Window]:
        """All windows, main and extra."""

        return self._windows.copy()

    @property
    def main_window(self) -> Window | None:
        """
        The main window, or `None` if the app has no windows (headless mode).\n
        Use `app.window` for a version of this property that can't be `None`.
        """

        if self._windows:
            return self._windows[0]

        return None

    @property
    def extra_windows(self) -> Sequence[Window]:
        """All windows that aren't the main window."""

        return self._windows[1:]

    @property
    def spec(self) -> WindowSpec | None:
        """The main window's spec, or `None` if the app is headless."""

        return self.app.spec.window_spec

    @property
    def monitors(self) -> Sequence[Monitor]:
        """Information about all connected monitors."""

        return self._monitors.copy()

    @property
    def primary_monitor(self) -> Monitor:
        """Information about the primary monitor."""

        return first(
            filter_by_attrs(self._monitors, is_primary=True), default=self.monitors[0]
        )

    main_monitor = primary_monitor  # alias

    def add_window(self, /, *, spec: WindowSpec) -> Window:
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

    def remove_window(self, window: Window | pygame.Window, /) -> None:
        """
        Removes and destroys the specified window.\n
        Finds a window using its `underlying` property if a `pygame.Window` is passed.\n
        Simply closes the app if the main window is passed.

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
            self.app.quit()
            return

        self._windows.remove(win)
        win.destroy()

    def clear_extras(self) -> None:
        """Removes all windows except the main one."""

        for window in self.extra_windows:
            self.remove_window(window)

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

    def _initialize(self) -> None:
        assert self.spec

        self.add_window(spec=self.spec)

        self.app.teardown += self.clear_extras

        self.app.events.add_callback(
            pygame.WINDOWCLOSE, lambda e: self.remove_window(e.window)
        )
