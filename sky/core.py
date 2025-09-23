from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from typing import TYPE_CHECKING, Literal, final

from singleton_decorator import singleton as untyped_singleton  # type: ignore

from .utils import Vector2

if TYPE_CHECKING:
    from .app import App

__all__ = [
    "Component",
    "singleton",
]


@final
@dataclass
class WindowSpec:
    """Defines information the window needs to have before mainloop. If `position` is None, the window will be centered on the screen."""

    _: KW_ONLY
    title: str = "Sky Engine"
    position: Vector2 | None = None
    size: Vector2 = field(default_factory=lambda: Vector2(800, 600))
    resizable: bool = False
    fullscreen: bool = False
    borderless: bool = False
    backend: Literal["software", "opengl", "vulkan"] = "software"
    initialization: Literal["immediate", "deferred"] = "immediate"
    """Only valid for the main window. Whether to initialize the window immediately or wait until mainloop is called. This is useful for adding listeners to the window before the app is started."""

    def is_software(self) -> bool:
        """Whether the window is running on a software backend."""

        return self.backend == "software"

    def is_hardware(self) -> bool:
        """Whether the window is running on a hardware backend (OpenGL or Vulkan)."""

        return not self.is_software()


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

    app: App

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def update(self) -> None: ...


def singleton[T: type](cls: T) -> T:
    """Makes the decorated class a singleton while keeping its type."""

    return untyped_singleton(cls)  # type: ignore
