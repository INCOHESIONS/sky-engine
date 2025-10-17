from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Self, final, override

import pygame
from pygame.event import Event as PygameEvent
from screeninfo import Monitor, get_monitors

from ..core import Component, WindowSpec
from ..listenable import Listenable
from ..utils import Vector2, filter_by_attrs, first, get_by_attrs

if TYPE_CHECKING:
    from ..app import App


__all__ = ["Windowing"]


# kind of assuming both pygame and screeninfo use the same indexing system here to match monitors to refresh rates
# i don't have more than one monitor to be able to test this so idk
# pretty ugly but screeninfo doesn't provide refresh rates so it is what it is
@final
@dataclass(slots=True, frozen=True)
class _MonitorInfo:
    name: str
    position: Vector2
    size: Vector2
    is_primary: bool
    index: int

    @classmethod
    def from_monitor(cls, monitor: Monitor, /, *, index: int) -> Self:
        """Creates a _MonitorInfo object from a screeninfo.Monitor object."""

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
    app: ClassVar[App]
    windowing: ClassVar[Windowing]

    _magic_fullscreen_position: ClassVar = Vector2(-8, -31)
    _magic_size_offset: ClassVar = Vector2(16, 39)

    def __init__(self, /, *, spec: WindowSpec) -> None:
        self._fullscreen = False
        self._minimized = False
        self._maximized = False

        if spec.state != "windowed":
            setattr(self, f"_{spec.state}", True)

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

        self._spec = spec
        self._icon = spec.icon

        self.on_render = Listenable()

        if spec.position is None:
            self.center_on_monitor()

        if spec.icon is not None:
            self.icon = spec.icon

    @property
    def spec(self) -> WindowSpec:
        """The window spec."""

        return self._spec

    @property
    def underlying(self) -> pygame.Window:
        """
        The underlying pygame window.\n
        Position, size and fullscreen, minimized and maximized states should not be modified directly through this property.
        """

        return self._underlying

    @property
    def surface(self) -> pygame.Surface:
        """The main window's surface."""

        return self._underlying.get_surface()

    @property
    def is_closed(self) -> bool:
        """Whether the window is closed."""

        try:
            _ = self.surface
        except pygame.error:
            return True

        return False

    @property
    def title(self) -> str:
        return self._underlying.title

    @title.setter
    def title(self, value: str) -> None:
        self._underlying.title = value

    @property
    def position(self) -> Vector2:
        """Gets or sets the position of the main window."""

        return Vector2(self._underlying.position)

    @position.setter
    def position(self, value: Vector2, /) -> None:
        self._underlying.position = value

    @property
    def size(self) -> Vector2:
        """Gets or sets the current size of the main window."""

        return Vector2(self._underlying.size)

    @size.setter
    def size(self, value: Vector2, /) -> None:
        self._underlying.size = value

    @property
    def width(self) -> int:
        """Gets the width of the main window."""

        return int(self.size.x)

    @width.setter
    def width(self, value: int, /) -> None:
        self._underlying.size = Vector2(value, self.height)

    @property
    def height(self) -> int:
        """Gets the height of the main window."""

        return int(self.size.y)

    @height.setter
    def height(self, value: int, /) -> None:
        self._underlying.size = Vector2(self.width, value)

    @property
    def rect(self) -> pygame.Rect:
        """The main window's rect."""

        return self.surface.get_rect()

    @property
    def center(self) -> Vector2:
        """Gets the center position, in pixel coordinates, of this window."""

        return self.size / 2

    @property
    def icon(self) -> pygame.Surface | None:
        """
        Gets or sets the icon of the main window.\n
        Returns `None` if the default icon is being used.
        """

        return self._icon

    @icon.setter
    def icon(self, value: pygame.Surface, /) -> None:
        self._icon = value
        self._underlying.set_icon(value)

    @property
    def fullscreen(self) -> bool:
        """
        Gets or sets the main window's fullscreen state.\n
        Does some extra magic on Windows to get fullscreening to work, unlike `pygame.Window`'s `set_fullscreen` method.
        """

        return self._fullscreen

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
        return self._minimized

    @minimized.setter
    def minimized(self, value: bool, /) -> None:
        self._minimized = value

        if value:
            self.underlying.minimize()
        else:
            self.underlying.restore()

    @property
    def maximized(self) -> bool:
        return self._maximized

    @maximized.setter
    def maximized(self, value: bool, /) -> None:
        self._maximized = value

        if value:
            self.underlying.maximize()
        else:
            self.underlying.restore()

    @property
    def borderless(self) -> bool:
        return self._underlying.borderless

    @borderless.setter
    def borderless(self, value: bool) -> None:
        self._underlying.borderless = value

    @property
    def resizable(self) -> bool:
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

    def center_on_monitor(self, monitor: _MonitorInfo | None = None, /) -> None:
        """Centers the window on the specified monitor, or the primary monitor if `None` is provided."""

        self.position = (
            monitor or self.windowing.primary_monitor
        ).size / 2 - self.size / 2

    def destroy(self) -> None:
        """Destroys the window."""

        self._underlying.destroy()
        self.on_render.clear()

    def flip(self) -> None:
        """Updates the window."""

        self._underlying.flip()

    update = flip


@final
class Windowing(Component):
    """Handles windowing."""

    WINDOWFULLSCREENED = pygame.USEREVENT + 1

    def __init__(self) -> None:
        _WindowWrapper.app = self.app
        _WindowWrapper.windowing = self

        self._main = None
        self._extras: list[_WindowWrapper] = []

        self._monitors = [
            _MonitorInfo.from_monitor(monitor, index=i)
            for i, monitor in enumerate(get_monitors())
        ]

        if self.spec and self.spec.initialization == "immediate":
            self._initialize()

    @property
    def main_window(self) -> _WindowWrapper | None:
        """
        The main window, or `None` if the app is headless.\n
        Use `app.window` for a version of this property that can't be `None`.
        """

        return self._main

    @property
    def all_windows(self) -> list[_WindowWrapper]:
        """All windows, including the main window."""

        return self._extras if self._main is None else [self._main] + self._extras

    @property
    def extra_windows(self) -> list[_WindowWrapper]:
        """All extra windows."""

        return self._extras

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

        return first(
            filter_by_attrs(self._monitors, is_primary=True), default=self.monitors[0]
        )

    @override
    def start(self) -> None:
        if self.spec and self.spec.initialization == "deferred":
            self._initialize()

    @override
    def update(self) -> None:
        for window in self.all_windows:
            window.on_render.notify()

    @override
    def stop(self) -> None:
        for window in self.all_windows:
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

        self._extras.remove(
            get_by_attrs(self._extras, _underlying=window)
            if isinstance(window, pygame.Window)
            else window  # pyright: ignore[reportArgumentType]
        )
        window.destroy()

    def clear_extras(self) -> None:
        """Removes all extra windows."""

        for window in self._extras:
            self.remove_extra(window)

    def _initialize(self) -> None:
        assert self.spec

        self._main = _WindowWrapper(spec=self.spec)

        self.app.post_update += self._post_update
        self.app.teardown += self.clear_extras

        self.app.events.on_event += self._handle_close

    # uses post_update to guarantee the window is flipped after any user-added components update
    def _post_update(self) -> None:
        for window in self.all_windows:
            window.flip()

    def _handle_close(self, event: pygame.event.Event, /) -> None:
        if event.type != pygame.WINDOWCLOSE:
            return

        assert self.main_window

        if event.window == self.main_window.underlying:
            self.app.quit()
        else:
            self.remove_extra(event.window)
