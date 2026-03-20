"""Contains the `Window` class, a `pygame.Window` wrapper with many utilities."""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, ClassVar, final, override

import pygame
from pygame import Rect as PygameRect

from ._managers import Keyboard, Mouse
from .core import InputManager, Monitor
from .hook import Hook
from .spec import WindowSpec
from .types import PygameEvent
from .utils import Color, Rect, Vector2, first

if TYPE_CHECKING:
    from ._services import Windowing
    from .app import App


if os.name == "nt":
    import win32api
    import win32con
    import win32gui
else:
    win32gui = win32con = win32api = None

__all__ = ["Window"]


@final
class Window:
    """Wrapper class for `pygame.Window` with many utilities."""

    app: ClassVar[App]
    windowing: ClassVar[Windowing]

    _magic_fullscreen_position: ClassVar = Vector2(-8, -31)
    _magic_size_offset: ClassVar = Vector2(16, 39)

    def __init__(self, /, *, spec: WindowSpec) -> None:
        self._spec = spec

        self._minimized = spec.state == "minimized"
        self._maximized = spec.state == "maximized"

        self._underlying = pygame.Window(
            title=spec.title,
            size=spec.size,
            resizable=spec.resizable,
            borderless=spec.borderless,
            always_on_top=spec.always_on_top,
            position=spec.position or (0, 0),
            opengl=spec.graphics_api == "opengl",
            vulkan=spec.graphics_api == "vulkan",
            maximized=self._maximized,
            minimized=self._minimized,
        )

        if spec.use_surface:
            _ = self._underlying.get_surface()

        self._fullscreen = spec.state == "fullscreen"

        if self._fullscreen:
            self.app.on_preload += lambda: setattr(self, "fullscreen", True)

        if self._spec.position is None:
            self.center_on_monitor()

        self._icon = self._spec.icon
        if self._spec.icon is not None:
            self.icon = self._spec.icon

        self.fill_color = self._spec.fill

        self.app.pre_update += self._pre_update
        self.app.events.on_event += self._handle_events

        self._should_flip = self._spec.flip

        if self._spec.flip:
            self.app.post_update += self.flip

        if self._spec.transparency_color is not None:
            self._handle_transparency()

        self._hook_map: dict[int, Hook[[PygameEvent]]] = {}

        self._setup_hooks()

        self._input_managers = [im(self) for im in spec.input_managers]

        self._keyboard = first(
            im for im in self._input_managers if isinstance(im, Keyboard)
        )
        self._mouse = first(im for im in self._input_managers if isinstance(im, Mouse))

    @override
    def __eq__(self, other: Any, /) -> bool:
        return (
            isinstance(other, self.__class__)
            and other.id == self.id
            or isinstance(other, pygame.Window)
            and other.id == self.id
        )

    @property
    def input_managers(self) -> Sequence[InputManager]:
        """This `Window`'s input managers."""

        return self._input_managers.copy()

    @property
    def keyboard(self) -> Keyboard:
        """
        This `Window`'s input manager for the keyboard.

        Raises
        ------
        `AssertionError`
            If no input manager was found, i.e., it wasn't included in this `Window`'s spec.
        """

        assert self._keyboard
        return self._keyboard

    @property
    def mouse(self) -> Mouse:
        """
        This `Window`'s input manager for the mouse.

        Raises
        ------
        `AssertionError`
            If no input manager was found, i.e., it wasn't included in this `Window`'s spec.
        """

        assert self._mouse
        return self._mouse

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
    def handle(self) -> int:
        """
        The window handle.\n
        Only available on Windows. Will return -1 on other platforms.
        """

        return win32gui.FindWindow(None, self.title) if win32gui else -1

    hwnd = handle  # alias

    @property
    def id(self) -> int:
        """This `Window`'s unique ID."""

        return self.underlying.id

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
    def should_flip(self) -> bool:
        return self._should_flip

    @should_flip.setter
    def should_flip(self, value: bool, /) -> None:
        self._should_flip = value

        if value and self.flip not in self.app.post_update:
            self.app.post_update += self.flip

        if not value and self.flip in self.app.post_update:
            self.app.post_update -= self.flip

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
    def rect(self) -> Rect:
        """This `Window`'s rect."""

        return Rect(self.surface.get_rect())

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

        if os.name == "nt":
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
        else:
            self._underlying.set_fullscreen(value)

        if value:
            self.app.events.post(
                PygameEvent(
                    self.windowing.WINDOWFULLSCREENED, dict(window=self.underlying)
                )
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

    @property
    def focused(self) -> bool:
        """Whether or not the window is focused."""

        return self.underlying.focused

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

    def focus(self) -> None:
        """Focuses the window."""

        self.underlying.focus()

    def fill(self, color: Color, /) -> None:
        """Fills the window with the specified color."""

        self.surface.fill(color)

    def blit(
        self, surface: pygame.Surface, /, position: Vector2 | PygameRect | Rect
    ) -> None:
        """Blits the surface onto the window."""

        self.surface.blit(surface, position)

    def destroy(self) -> None:
        """Destroys the window."""

        if self is self.windowing.main_window:
            self.app.quit()

        self.windowing._windows.remove(self)  # pyright: ignore[reportPrivateUsage]

        self.before_destroy.notify()

        self._underlying.destroy()

        self.app.pre_update -= self._pre_update

        if self.flip in self.app.post_update:
            self.app.post_update -= self.flip

        self.on_render.clear()

        self.after_destroy.notify()

    def flip(self) -> None:
        """Updates the window."""

        self._underlying.flip()

    update = flip

    def _pre_update(self) -> None:
        if self.fill_color:
            self.fill(self.fill_color)

    def _setup_hooks(self) -> None:
        self.on_render = Hook()

        self.before_destroy = Hook()
        self.after_destroy = Hook()

        self.on_mouse_enter = self._make_event_hook(pygame.WINDOWENTER)
        self.on_mouse_leave = self._make_event_hook(pygame.WINDOWLEAVE)
        self.on_mouse_move = self._make_event_hook(pygame.MOUSEMOTION)

        self.on_focus_gained = self._make_event_hook(pygame.WINDOWFOCUSGAINED)
        self.on_focus_lost = self._make_event_hook(pygame.WINDOWFOCUSLOST)

        self.on_resize = self._make_event_hook(pygame.WINDOWRESIZED)
        self.on_fullscreen = self._make_event_hook(self.windowing.WINDOWFULLSCREENED)

    def _handle_transparency(self) -> None:
        if win32gui is None or win32con is None or win32api is None:
            raise OSError("This method is only supported on Windows.")

        assert self.spec.transparency_color

        win32gui.SetWindowLong(  # pyright: ignore[reportUnknownMemberType]
            self.handle,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(self.handle, win32con.GWL_EXSTYLE)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            | win32con.WS_EX_LAYERED,
        )

        win32gui.SetLayeredWindowAttributes(  # pyright: ignore[reportUnknownMemberType]
            self.handle,
            win32api.RGB(*self.spec.transparency_color.rgb),
            0,
            win32con.LWA_COLORKEY,
        )

    def _handle_events(self, event: pygame.event.Event, /):
        if not hasattr(event, "window") or event.window != self.underlying:
            return

        if event.type == pygame.WINDOWCLOSE:
            self.destroy()
            return

        if event.type in self._hook_map:
            self._hook_map[event.type].notify(event)

    def _make_event_hook(self, type: int, /) -> Hook[[PygameEvent]]:
        self._hook_map[type] = Hook[[PygameEvent]]()
        return self._hook_map[type]
