from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from typing import Literal, final

from .utils import Vector2

__all__ = ["AppSpec", "WindowSpec"]


@final
@dataclass
class WindowSpec:
    """Defines information the window needs to have before mainloop.If position is None, the window will be centered on the screen."""

    _: KW_ONLY
    title: str = "Sky Engine"
    position: Vector2 | None = None
    size: Vector2 = field(default_factory=lambda: Vector2(800, 600))
    resizable: bool = False
    fullscreen: bool = False
    borderless: bool = False
    backend: Literal["software", "opengl", "vulkan"] = "software"

    def is_software(self) -> bool:
        return self.backend == "software"

    def is_hardware(self) -> bool:
        return not self.is_software()


@final
@dataclass
class AppSpec:
    """Defines information the app needs to have before mainloop. If window_spec is None, a window will not be created."""

    _: KW_ONLY
    window_spec: WindowSpec | None = field(default_factory=WindowSpec)

    @classmethod
    def headless(cls) -> AppSpec:
        """Simply creates an AppSpec with window_spec set to None."""

        return cls(window_spec=None)
