"""Contains the `Window` class, a `pygame.Window` wrapper with many utilities."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Callable, ClassVar, final

import pygame
from pygame.event import Event as PygameEvent

from .core import Monitor
from .hook import Hook
from .spec import WindowSpec
from .utils import Color, Vector2

if TYPE_CHECKING:
    from ._services.windowing import Windowing
    from .app import App

__all__ = ["Window"]


type _PygameEventCallback = Callable[[PygameEvent], None]


@final
class Window:
    """Wrapper class for `pygame.Window` with many utilities."""

    app: ClassVar[App]
    windowing: ClassVar[Windowing]

    _magic_fullscreen_position: ClassVar[Vector2] = Vector2(-8, -31)
    _magic_size_offset: ClassVar[Vector2] = Vector2(16, 39)

    def __init__(self, /, *, spec: WindowSpec) -> None:
        self._spec = spec

        self._underlying = pygame.Window(
            position=spec.position or (0, 0),
            opengl=spec.backend == "opengl",
            vulkan=spec.backend == "vulkan",
            **{spec.state: True} if spec.state != "windowed" else {},
            **{
                name: getattr(spec, name)
                for name in (
                    "title",
                    "size",
                    "resizable",
                    "borderless",
                )
            },
        )
        _ = self._underlying.get_surface()  # necessary

        self._fullscreen = False
        self._minimized = False
        self._maximized = False

        if self._spec.state != "windowed":
            setattr(self, f"_{self._spec.state}", True)

        if self._spec.position is None:
            self.center_on_monitor()

        self._icon = self._spec.icon
        if self._spec.icon is not None:
            self.icon = self._spec.icon

        self.fill_color = self._spec.fill

        self._hook_map: dict[int, Hook[_PygameEventCallback]] = {}

        self.on_render = Hook()

        self.on_mouse_enter = self._make_hook(pygame.WINDOWENTER)
        self.on_mouse_leave = self._make_hook(pygame.WINDOWLEAVE)
        self.on_mouse_move = self._make_hook(pygame.MOUSEMOTION)

        self.on_focus_gained = self._make_hook(pygame.WINDOWFOCUSGAINED)
        self.on_focus_lost = self._make_hook(pygame.WINDOWFOCUSLOST)

        self.on_resize = self._make_hook(pygame.WINDOWRESIZED)
        self.on_close = self._make_hook(pygame.WINDOWCLOSE)

        self.app.pre_update += self._pre_update
        self.app.post_update += self.flip
        self.app.events.on_event += self._handle_events

    @property
    def spec(self) -> WindowSpec:
        """The window spec."""

        return self._spec

    @property
    def underlying(self) -> pygame.Window:
        """
        The underlying `pygame.Window`.\n
        Position, size and fullscreen, minimized and maximized states should not be modified directly through this property.\n
        Use carefully.
        """

        return self._underlying

    @property
    def surface(self) -> pygame.Surface:
        """This `Window`'s surface."""

        return self._underlying.get_surface()

    @property
    def is_open(self) -> bool:
        """Whether this window is open."""

        try:
            _ = self.surface
        except pygame.error:
            return False

        return True

    @property
    def is_closed(self) -> bool:
        """Whether this window is closed."""

        return not self.is_open

    @property
    def title(self) -> str:
        """This `Window`'s title."""

        return self._underlying.title

    @title.setter
    def title(self, value: str) -> None:
        self._underlying.title = value

    @property
    def position(self) -> Vector2:
        """This `Window`'s position."""

        return Vector2(self._underlying.position)

    @position.setter
    def position(self, value: Vector2, /) -> None:
        self._underlying.position = value

    @property
    def size(self) -> Vector2:
        """This `Window`'s size."""

        return Vector2(self._underlying.size)

    @size.setter
    def size(self, value: Vector2, /) -> None:
        self._underlying.size = value

    @property
    def width(self) -> int:
        """This `Window`'s width."""

        return int(self.size.x)

    @width.setter
    def width(self, value: int, /) -> None:
        self._underlying.size = Vector2(value, self.height)

    @property
    def height(self) -> int:
        """This `Window`'s height."""

        return int(self.size.y)

    @height.setter
    def height(self, value: int, /) -> None:
        self._underlying.size = Vector2(self.width, value)

    @property
    def rect(self) -> pygame.Rect:
        """This `Window`'s rect."""

        return self.surface.get_rect()

    @property
    def center(self) -> Vector2:
        """This `Window`'s center pixel."""

        return self.size / 2

    @property
    def icon(self) -> pygame.Surface | None:
        """This `Window`'s icon. `None` if the default icon is being used."""

        return self._icon

    @icon.setter
    def icon(self, value: pygame.Surface, /) -> None:
        self._icon = value
        self._underlying.set_icon(value)

    @property
    def fullscreen(self) -> bool:
        """
        Whether or not this window is fullscreened.\n
        Does some extra magic on Windows to get fullscreening to work, unlike `pygame.Window`'s `set_fullscreen` method.
        """

        return self._fullscreen  # FIXME: MAY RETURN INCORRECT VALUES

    @fullscreen.setter
    def fullscreen(self, value: bool, /) -> None:
        self._fullscreen = value

        if os.name != "nt":
            self._underlying.set_fullscreen(value)

        # this is based on some old code i wrote to fix fullscreening problems with pygame.
        # i don't really know what the magic numbers mean, i just know that they work.
        # well, mostly. at least they do on my machine

        self.size = (
            (self.windowing.primary_monitor.size + self._magic_size_offset)
            if value
            else self._spec.size
        )

        if value:
            self.position = self._magic_fullscreen_position
        else:
            self.center_on_monitor()

        self.app.events.post(
            PygameEvent(self.windowing.WINDOWFULLSCREENED, dict(window=self.underlying))
        )

    @property
    def minimized(self) -> bool:
        """Whether or not the window is minimized."""

        return self._minimized  # FIXME: MAY RETURN INCORRECT VALUES

    @minimized.setter
    def minimized(self, value: bool, /) -> None:
        self._minimized = value

        if value:
            self.underlying.minimize()
        else:
            self.underlying.restore()

    @property
    def maximized(self) -> bool:
        """Whether or not the window is maximized."""

        return self._maximized  # FIXME: MAY RETURN INCORRECT VALUES

    @maximized.setter
    def maximized(self, value: bool, /) -> None:
        self._maximized = value

        if value:
            self.underlying.maximize()
        else:
            self.underlying.restore()

    @property
    def borderless(self) -> bool:
        """Whether or not the window is borderless."""

        return self._underlying.borderless

    @borderless.setter
    def borderless(self, value: bool) -> None:
        self._underlying.borderless = value

    @property
    def resizable(self) -> bool:
        """Whether or not the window is resizable."""

        return self._underlying.resizable

    @resizable.setter
    def resizable(self, value: bool) -> None:
        self._underlying.resizable = value

    def toggle_fullscreen(self, /, *, borderless: bool = False) -> None:
        """Toggles fullscreen mode."""

        self.fullscreen = not self._fullscreen

        if borderless:
            self.borderless = self.fullscreen

    def toggle_minimized(self) -> None:
        """Toggles minimized mode."""

        self.minimized = not self._minimized

    def toggle_maximized(self) -> None:
        """Toggles maximized mode."""

        self.maximized = not self._maximized

    def center_on_monitor(self, monitor: Monitor | None = None, /) -> None:
        """Centers the window on the specified monitor, or the primary monitor if `None` is provided."""

        self.position = (
            monitor or self.windowing.primary_monitor
        ).size / 2 - self.size / 2

    def fill(self, color: Color, /) -> None:
        """Fills the window with the specified color."""

        self.surface.fill(color)

    def blit(self, surface: pygame.Surface, /, position: Vector2 | pygame.Rect) -> None:
        """Blits the surface onto the window."""

        self.surface.blit(surface, position)

    def destroy(self) -> None:
        """Destroys the window."""

        self._underlying.destroy()

        self.app.pre_update -= self._pre_update
        self.app.post_update -= self.flip

        self.on_render.clear()
        self.on_close.notify()

    def flip(self) -> None:
        """Updates the window."""

        self._underlying.flip()

    update = flip

    def _pre_update(self) -> None:
        if self.fill_color:
            self.fill(self.fill_color)

    def _handle_events(self, event: pygame.event.Event):
        if not hasattr(event, "window") or event.window != self.underlying:
            return

        if event.type in self._hook_map:
            self._hook_map[event.type].notify(event)

    def _make_hook(self, type: int) -> Hook[_PygameEventCallback]:
        self._hook_map[type] = Hook[_PygameEventCallback]()
        return self._hook_map[type]
