from ctypes import windll
from typing import override

import pygame
import win32gui

from ..core import Component
from ..spec import Backend, WindowSpec
from ..utils import Vector2

__all__ = ["Windowing"]


class Windowing(Component):
    """Handles windowing."""

    _magic_fullscreen_position = Vector2(-8, -31)
    _magic_size_offset = Vector2(16, 39)

    def __init__(self) -> None:
        self._main_window = None
        self._should_flip = self.spec.backend.is_software()
        self._fullscreen = self.spec.fullscreen

        self._main_monitor_index = 0
        self._monitors = pygame.display.get_desktop_sizes()

        self.app.post_update += self.post_update

    @property
    def main_monitor_size(self) -> Vector2:
        """The size of the main monitor."""
        return self.monitor_sizes[self._main_monitor_index]

    @property
    def monitor_sizes(self) -> tuple[Vector2, ...]:
        """The sizes of all connected monitors."""
        return tuple(map(Vector2, self._monitors))

    @property
    def spec(self) -> WindowSpec:
        """The window spec."""
        return self.app.spec.window_spec

    @property
    def window(self) -> pygame.Window | None:
        """The main window, or None if the app is not running."""
        return self._main_window

    @property
    def surface(self) -> pygame.Surface | None:
        """The main window's surface."""

        return self.window.get_surface() if self.window else None

    @property
    def position(self) -> Vector2:
        """
        The position of the main window.

        Raises
        ------
        AssertionError
            If the main window is not set.
        """
        assert self._main_window is not None
        return Vector2(self._main_window.position)

    @position.setter
    def position(self, value: Vector2) -> None:
        """
        Sets the position of the main window, with some magic to fix fullscreening problems.

        Parameters
        ----------
        value: Vector2
            The new position.

        Raises
        ------
        AssertionError
            If the main window is not set.
        """
        # this is based on some old code i wrote to fix fullscreening problems with pygame.
        # i don't really know what the magic numbers mean, i just know that they work.
        # well, mostly. at least they do on my machine
        assert self._main_window is not None
        handle = win32gui.FindWindow(None, self._main_window.title)
        windll.user32.MoveWindow(
            handle,
            *value.to_int_tuple(),
            *(self.size + self._magic_size_offset).to_int_tuple(),
        )

    @property
    def size(self) -> Vector2:
        """
        The current size of the main window if the app is running, or the size in the spec otherwise.
        """
        return Vector2(
            self._main_window.size if self._main_window is not None else self.spec.size
        )

    @size.setter
    def size(self, value: Vector2) -> None:
        """
        Sets the size of the main window.

        Parameters
        ----------
        value: Vector2
            The new size.

        Raises
        ------
        AssertionError
            If the main window is not set.
        """
        assert self._main_window is not None
        self._main_window.size = value

    @property
    def fullscreen(self) -> bool:
        """Whether the main window is fullscreen or not."""
        return self._fullscreen

    @fullscreen.setter
    def fullscreen(self, value: bool) -> None:
        """
        Sets whether the main window is fullscreen or not.
        Probably the only part in the library that's currently not cross-platform.

        Parameters
        ----------
        value: bool
            Whether to set the window to fullscreen or not.

        Raises
        ------
        AssertionError
            If the main window is not set.
        """
        assert self._main_window is not None
        self._fullscreen = value
        self.position = (
            self._magic_fullscreen_position if value else self._centered_window_pos()
        )
        self.size = self.main_monitor_size if value else self.spec.size

    @override
    def start(self) -> None:
        self._main_window = pygame.Window(
            self.spec.title,
            self.spec.size,
            position=(self.spec.position or self._centered_window_pos()),
            fullscreen=self._fullscreen,
            resizable=self.spec.resizable,
            opengl=self.spec.backend == Backend.opengl,
            vulkan=self.spec.backend == Backend.vulkan,
        )

        self._main_window_surface = self._main_window.get_surface()

    @override
    def stop(self) -> None:
        if self._main_window is not None:
            self._main_window.destroy()

    # uses post_update to guarantee the window is flipped after any user-added components update
    def post_update(self) -> None:
        assert self._main_window is not None

        self._main_window.flip()

        if evt := self.app.events.get(pygame.WINDOWCLOSE):
            if evt.window == self._main_window:
                self._main_window.destroy()  # type: ignore
                self.app.quit()

    def toggle_fullscreen(self) -> None:
        """Toggles fullscreen mode."""
        self.fullscreen = not self._fullscreen

    def _centered_window_pos(self) -> Vector2:
        return self.main_monitor_size / 2 - self.size / 2
