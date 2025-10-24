"""Core engine functionality."""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from typing import TYPE_CHECKING, Callable, ClassVar, Literal, Self, final

from pygame import Surface
from singleton_decorator import (  # pyright: ignore[reportMissingTypeStubs]
    singleton as untyped_singleton,  # pyright: ignore[reportUnknownVariableType]
)

from .colors import BLACK
from .enums import Key, Modifier, State
from .hook import Hook
from .types import Coroutine
from .utils import Color, Vector2

if TYPE_CHECKING:
    from .app import App

__all__ = [
    "AppSpec",
    "Component",
    "Keybinding",
    "singleton",
    "WindowSpec",
]


@final
@dataclass(slots=True)
class Keybinding:
    """Defines a keybinding."""

    keys: dict[Key, State]
    on_activation: Hook = field(default_factory=Hook)
    on_deactivation: Hook = field(default_factory=Hook)

    def __post_init__(self):
        if not self.keys:
            raise ValueError("Keybinding must have at least one key")

    @classmethod
    def simple(
        cls,
        key: Key,
        /,
        *,
        action: Callable[[], None],
        state: State = State.downed,
    ) -> Self:
        """Creates a keybinding with a single key and an action."""

        return cls({key: state}, Hook([action]))

    @classmethod
    def modifier(
        cls,
        key: Key,
        /,
        modifier: Modifier,
        *,
        action: Callable[[], None],
        state: State = State.downed,
    ) -> Self:
        """Creates a keybinding that requires a modifier to be pressed."""

        return cls({modifier.value: State.pressed, key: state}, Hook([action]))


@final
@dataclass(slots=True, frozen=True)
class WindowSpec:
    """Defines information necessary to create a window."""

    _: KW_ONLY

    title: str = "Sky Engine"
    """The window's title. "Sky Engine" by default."""

    position: Vector2 | None = None
    """The window's position. Centers it on the main monitor by default."""

    size: Vector2 = field(default_factory=lambda: Vector2(800, 600))
    """The window's size. 800x600 by default."""

    icon: Surface | None = None
    """The window's icon. Uses the default pygame icon if `None`."""

    resizable: bool = False
    """Whether or not the window can be resized. Posts a pygame.WINDOWRESIZED event whenever resized."""

    borderless: bool = False
    """Whether or not the window is borderless, which also means it has no decorations."""

    fill: Color | None = field(default_factory=lambda: BLACK)
    """The window's fill color. If `None`, `fill` will not be called on `pre_update`"""

    state: Literal["windowed", "minimized", "maximized", "fullscreen"] = "windowed"
    """What state the window should be initialized at. Defaults to windowed."""

    backend: Literal["software", "opengl", "vulkan"] = "software"
    """The backend to use for the window. Software by default."""

    initialization: Literal["immediate", "deferred"] = "immediate"
    """Whether or not the main window should be initialized immediately or wait until `mainloop` is called. This is useful for adding callbacks to the window before the app has started."""

    @property
    def is_software(self) -> bool:
        """Whether the window is running on a software backend."""

        return self.backend == "software"

    @property
    def is_hardware(self) -> bool:
        """Whether the window is running on a hardware backend (OpenGL or Vulkan)."""

        return not self.is_software


@final
@dataclass(slots=True, frozen=True)
class AppSpec:
    """Defines information the app needs to have before mainloop. If `window_spec` is None, a window will not be created (headless mode)."""

    _: KW_ONLY

    window_spec: WindowSpec | None = field(default_factory=WindowSpec)
    """The main window's `WindowSpec`"""

    # general debugging flag that currently does nothing internally
    debug: bool = False
    """Whether to enable debugging."""

    profile: bool = False
    """Whether to enable profiling (using `cProfile`)."""

    @classmethod
    def headless(cls) -> AppSpec:
        """Simply creates an `AppSpec` with `window_spec` set to None."""

        return cls(window_spec=None)


class Component:
    """Base class for components."""

    app: ClassVar[App]

    def start(self) -> Coroutine | None:
        """Runs before the first frame, after `entrypoint` and before `setup`. Can be a Coroutine."""

    def stop(self) -> Coroutine | None:
        """Runs after the last frame, after `teardown` and before `cleanup`. Can be a Coroutine."""

    def update(self) -> None:
        """Runs every frame, after `pre_update` and before `post_update`."""


def singleton[T: type](cls: T) -> T:
    """Makes the decorated class a singleton while properly keeping its type."""

    return untyped_singleton(cls)  # pyright: ignore[reportReturnType]
