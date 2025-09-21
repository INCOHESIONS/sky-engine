import os
from typing import override

import pygame

from ..core import Component
from ..spec import WindowSpec
from ..utils import Vector2

if os.name == "nt":
    from ctypes import windll

    import win32gui


__all__ = ["Windowing"]


class Windowing(Component):
    """Handles windowing."""

    _magic_fullscreen_position = Vector2(-8, -31)
    _magic_size_offset = Vector2(16, 39)

    def __init__(self) -> None:
        self._main = None

        if self.spec is None:
            self._should_flip = False
            self._fullscreen = False
        else:
            self._should_flip = self.spec.is_software()
            self._fullscreen = self.spec.fullscreen

        self._main_monitor_index = 0
        self._monitors = pygame.display.get_desktop_sizes()

    @property
    def main_monitor_size(self) -> Vector2:
        """The size of the main monitor."""

        return self.monitor_sizes[self._main_monitor_index]

    @property
    def monitor_sizes(self) -> tuple[Vector2, ...]:
        """The sizes of all connected monitors."""

        return tuple(map(Vector2, self._monitors))

    @property
    def spec(self) -> WindowSpec | None:
        """The window spec."""

        return self.app.spec.window_spec

    @property
    def surface(self) -> pygame.Surface | None:
        """The main window's surface."""

        return self._main.get_surface() if self._main else None

    @property
    def position(self) -> Vector2:
        """
        Gets or sets the position of the main window.

        # Getter

        Returns
        -------
        `Vector2`
            The position of the main window.

        Raises
        ------
        `AssertionError`
            If the main window is not set.

        # Setter

        Parameters
        ----------
        value: `Vector2`
            The new position. Uses some magic to fix fullscreening problems.

        Raises
        ------
        `AssertionError`
            If the main window is not set.
        """

        assert self._main is not None
        return Vector2(self._main.position)

    @position.setter
    def position(self, value: Vector2) -> None:
        # this is based on some old code i wrote to fix fullscreening problems with pygame.
        # i don't really know what the magic numbers mean, i just know that they work.
        # well, mostly. at least they do on my machine
        assert self._main is not None

        if os.name == "nt":
            windll.user32.MoveWindow(
                win32gui.FindWindow(None, self._main.title),
                *value.to_int_tuple(),
                *(self.size + self._magic_size_offset).to_int_tuple(),
            )
            return

        self._main.position = value

    @property
    def size(self) -> Vector2:
        """
        Gets or sets the current size of the main window.

        # Getter
        If the app is running, or the size in the spec otherwise.

        Returns
        -------
        `Vector2`
            The current size of the main window.

        Raises
        ------
        `AssertionError`
            If the spec is not set.

        # Setter

        Parameters
        ----------
        value: `Vector2`
            The new size.

        Raises
        ------
        `AssertionError`
            If the main window is not set.
        """

        assert self.spec is not None
        return Vector2(self._main.size if self._main is not None else self.spec.size)

    @size.setter
    def size(self, value: Vector2) -> None:
        assert self._main is not None
        self._main.size = value

    @property
    def fullscreen(self) -> bool:
        """
        Gets or sets the main window's fullscreen state.

        # Getter

        Returns
        -------
        `bool`
            Whether the main window is fullscreen or not.\n
            Returns whatever is on the spec if the app is not running, or `False` if in headless mode.

        # Setter

        Parameters
        ----------
        value: `bool`
            Whether to set the window to fullscreen or not.

        Raises
        ------
        `AssertionError`
            If the main window is not set.
        """

        return self._fullscreen

    @fullscreen.setter
    def fullscreen(self, value: bool) -> None:
        assert self._main is not None and self.spec is not None
        self._fullscreen = value

        if os.name != "nt":
            self._main.set_fullscreen(value)

        self.position = (
            self._magic_fullscreen_position if value else self._centered_window_pos
        )
        self.size = self.main_monitor_size if value else self.spec.size

    @property
    def _centered_window_pos(self) -> Vector2:
        return self.main_monitor_size / 2 - self.size / 2

    @override
    def start(self) -> None:
        if self.spec is None:
            return

        self._main = pygame.Window(
            self.spec.title,
            self.spec.size,
            position=(self.spec.position or self._centered_window_pos),
            fullscreen=self._fullscreen,
            resizable=self.spec.resizable,
            borderless=self.spec.borderless,
            opengl=self.spec.backend == "opengl",
            vulkan=self.spec.backend == "vulkan",
        )

        self._main.get_surface()

        self.app.post_update += self._post_update

    @override
    def stop(self) -> None:
        if self._main is not None:
            self._main.destroy()

    def toggle_fullscreen(self) -> None:
        """Toggles fullscreen mode."""

        self.fullscreen = not self._fullscreen

    # uses post_update to guarantee the window is flipped after any user-added components update
    def _post_update(self) -> None:
        if self._main is None:
            return

        self._main.flip()

        if evt := self.app.events.get(pygame.WINDOWCLOSE):
            if evt.window == self._main:
                self._main.destroy()  # type: ignore
                self.app.quit()
