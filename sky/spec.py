"""Specs, i.e. information necessary before execution."""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from typing import Literal, Self, final

from pygame import Surface

from .colors import BLACK
from .core import Component
from .utils import Color, Vector2

__all__ = [
    "AppSpec",
    "SceneSpec",
    "WindowSpec",
]


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
