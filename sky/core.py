"""Core engine functionality."""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from typing import TYPE_CHECKING, ClassVar, Literal, final

from pygame import Surface
from singleton_decorator import singleton as untyped_singleton  # pyright: ignore[reportUnknownVariableType, reportMissingTypeStubs]

from .types import Coroutine
from .utils import Vector2

if TYPE_CHECKING:
    from .app import App

__all__ = [
    "AppSpec",
    "Component",
    "singleton",
    "WindowSpec",
]


@final
@dataclass
class WindowSpec:
    """Defines information the window needs to have before mainloop. If `position` is None, the window will be centered on the screen."""

    _: KW_ONLY

    title: str = "Sky Engine"
    position: Vector2 | None = None
    size: Vector2 = field(default_factory=lambda: Vector2(800, 600))
    icon: Surface | None = None

    resizable: bool = False
    borderless: bool = False

    state: Literal["windowed", "minimized", "maximized", "fullscreen"] = "windowed"
    """What state the window should be initialized at. Defaults to windowed."""

    backend: Literal["software", "opengl", "vulkan"] = "software"
    """The backend to use for the window. Software by default."""

    initialization: Literal["immediate", "deferred"] = "immediate"
    """Only valid for the main window. Whether to initialize the window immediately or wait until `mainloop` is called. This is useful for adding listeners to the window before the app is started."""

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
class AppSpec:
    """Defines information the app needs to have before mainloop. If `window_spec` is None, a window will not be created."""

    _: KW_ONLY
    window_spec: WindowSpec | None = field(default_factory=WindowSpec)

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
