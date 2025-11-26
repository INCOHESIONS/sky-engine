from dataclasses import KW_ONLY, dataclass, field
from typing import Self, override

import pygame

from .core import StateColors, Style, UIElement


@dataclass(slots=True, frozen=True)
class ButtonStyle(Style):
    _: KW_ONLY

    fill_colors: StateColors | None = field(default_factory=StateColors)
    border_colors: StateColors | None = None
    border_radius: int = 10
    border_width: int = -1

    @override
    @classmethod
    def dark(cls) -> Self:
        raise NotImplementedError()  # TODO:

    @override
    @classmethod
    def high_contrast(cls) -> Self:
        raise NotImplementedError()  # TODO:


class Button(UIElement[ButtonStyle]):
    @override
    def render(self) -> None:
        if self.style.fill_colors:
            pygame.draw.rect(
                self.window.surface,
                self.style.fill_colors.calculate(element=self),
                self.bounds,
                border_radius=self.style.border_radius,
            )

        if self.style.border_colors:
            pygame.draw.rect(
                self.window.surface,
                self.style.border_colors.calculate(element=self),
                self.bounds,
                border_radius=self.style.border_radius,
                width=self.style.border_width,
            )
