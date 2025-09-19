from ctypes import windll
from typing import override

import pygame
import win32gui

from ..core import Component
from ..spec import Backend, WindowSpec
from ..utils import Vector2

__all__ = ["Windowing"]


class Windowing(Component):
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
    def main_window(self) -> pygame.Window | None:
        return self._main_window

    @property
    def main_monitor_size(self) -> Vector2:
        return self.monitor_sizes[self._main_monitor_index]

    @property
    def monitor_sizes(self) -> tuple[Vector2, ...]:
        return tuple(map(Vector2, self._monitors))

    @property
    def spec(self) -> WindowSpec:
        return self.app.spec.window_spec

    @property
    def position(self) -> Vector2:
        assert self._main_window is not None
        return Vector2(self._main_window.position)

    @position.setter
    def position(self, value: Vector2) -> None:
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
        return Vector2(
            self._main_window.size if self._main_window is not None else self.spec.size
        )

    @size.setter
    def size(self, value: Vector2) -> None:
        assert self._main_window is not None
        self._main_window.size = value

    @property
    def fullscreen(self) -> bool:
        return self._fullscreen

    @fullscreen.setter
    def fullscreen(self, value: bool) -> None:
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

    def post_update(self) -> None:
        assert self._main_window is not None

        self._main_window.flip()

        if evt := self.app.events.get(pygame.WINDOWCLOSE):
            if evt.window == self._main_window:
                self._main_window.destroy()  # type: ignore
                self.app.quit()

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self._fullscreen

    def _centered_window_pos(self) -> Vector2:
        return self.main_monitor_size / 2 - self.size / 2
