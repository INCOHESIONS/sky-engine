"""Specs, i.e. information necessary before the `App`'s execution."""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from typing import Literal, Protocol, Self, final

from pygame import Surface

from ._managers import Keyboard, Mouse
from .colors import BLACK
from .core import Component, InputManager
from .utils import Color, Vector2

__all__ = [
    "AppSpec",
    "SceneSpec",
    "WindowSpec",
]


class Module(Protocol):
    """
    A module protocol class to be loaded during `App` instancing using the `modules` argument in `AppSpec`.\n
    Requires `init` and `quit` methods that each take no arguments.\n
    Used for loading `pygame` modules such as `freetype` and `mixer`.
    """

    def init(self) -> None: ...

    def quit(self) -> None: ...


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

    always_on_top: bool = False
    """Whether or not the window is always on top."""

    use_surface: bool = True
    """Whether or not to call `get_surface` once the underlying window is created. Setting this to `False` is necessary to use pygame's new `_sdl2.video.Renderer` class."""

    transparency_color: Color | None = None
    """The window's transparency key color. All pixels that match this color will be colored transparent instead. Windows only."""

    flip: bool = True
    """Whether or not the window should be flipped on `post_update`, i.e., updated."""

    fill: Color | None = field(default_factory=lambda: BLACK)
    """The window's fill color. If `None`, `fill` will not be called on `pre_update`"""

    state: Literal["windowed", "minimized", "maximized", "fullscreen"] = "windowed"
    """What state the window should be initialized at. Defaults to windowed."""

    graphics_api: Literal["opengl", "vulkan"] | None = None
    """Enables support for an OpenGL context or a Vulkan instance."""

    initialization: Literal["immediate", "deferred"] = "immediate"
    """Whether or not the main window should be initialized immediately or wait until `mainloop` is called. This is useful for adding callbacks to the window before the app has started."""

    input_managers: list[type[InputManager]] = field(
        default_factory=lambda: [Keyboard, Mouse]
    )
    """The list of constructors for the input managers that will be updated every frame by this window. Includes `Keyboard` and `Mouse` by default."""


@final
@dataclass
class SceneSpec:
    """Defines information necessary to create a scene."""

    components: list[Component] = field(default_factory=list)
    """A list of components to add to the scene."""


@final
@dataclass(slots=True, frozen=True)
class AppSpec:
    """Defines information the app needs to have before mainloop. If `window_spec` is None, a window will not be created (headless mode)."""

    _: KW_ONLY

    window_spec: WindowSpec | None = field(default_factory=WindowSpec)
    """The main window's `WindowSpec`"""

    scene_spec: SceneSpec | None = field(default_factory=SceneSpec)
    """The default scene to add to the app. If `None`, will not create a default scene."""

    modules: list[Module] = field(default_factory=list)
    """A list of modules to add to the app. Modules must have a `init` and `quit` methods. Useful for initializing and cleaning up `pygame` modules such as `freetype` and `mixer`."""

    # general debugging flag that currently does nothing internally
    debug: bool = False
    """Whether to enable debugging."""

    profile: bool = False
    """Whether to enable profiling (using `cProfile`)."""

    @classmethod
    def headless(cls) -> Self:
        """Simply creates an `AppSpec` with `window_spec` set to `None`, meaning no window will be created."""

        return cls(window_spec=None)

    @classmethod
    def sceneless(cls) -> Self:
        """Simply creates an `AppSpec` with `scene_spec` set to `None`, meaning no scene will be created."""

        return cls(scene_spec=None)
