from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from enum import Enum, auto

from .utils import Vector2

__all__ = ["AppSpec", "Backend", "WindowSpec"]


class Backend(Enum):
    software = auto()
    opengl = auto()
    vulkan = auto()

    def is_software(self) -> bool:
        return self == Backend.software

    def is_hardware(self) -> bool:
        return not self.is_software()


@dataclass
class WindowSpec:
    _: KW_ONLY
    title: str = "Sky Engine"
    position: Vector2 | None = None
    size: Vector2 = field(default_factory=lambda: Vector2(800, 600))
    resizable: bool = True
    fullscreen: bool = False
    backend: Backend = Backend.software


@dataclass
class AppSpec:
    _: KW_ONLY
    window_spec: WindowSpec = field(default_factory=WindowSpec)
