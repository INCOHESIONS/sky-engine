from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from enum import Enum, auto

from .utils import Vector2

__all__ = ["AppSpec", "Backend", "WindowSpec"]


class Backend(Enum):
    """What backend to use for the window. Should be set according to what rendering backend is used."""

    software = auto()
    opengl = auto()
    vulkan = auto()

    def is_software(self) -> bool:
        return self == Backend.software

    def is_hardware(self) -> bool:
        return not self.is_software()


@dataclass
class WindowSpec:
    """Defines information the window needs to have before mainloop."""

    _: KW_ONLY
    title: str = "Sky Engine"
    position: Vector2 | None = None
    size: Vector2 = field(default_factory=lambda: Vector2(800, 600))
    resizable: bool = True
    fullscreen: bool = False
    backend: Backend = Backend.software


@dataclass
class AppSpec:
    """Defines information the app needs to have before mainloop. If window_spec is None, a window will not be created."""

    _: KW_ONLY
    window_spec: WindowSpec | None = field(default_factory=WindowSpec)

    @classmethod
    def headless(cls) -> AppSpec:
        """Simply creates an AppSpec with window_spec set to None."""

        return cls(window_spec=None)
