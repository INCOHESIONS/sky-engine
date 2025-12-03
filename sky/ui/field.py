"""Basic, extensible `Field` `UIElement` that uses `pygame.draw` for rendering."""

from dataclasses import KW_ONLY, dataclass, field
from enum import Enum
from typing import Self, override

from pygame.freetype import SysFont as get_system_font

from ..colors import BLACK, WHITE, YELLOW
from ..hook import Hook
from ..utils import Rect, Vector2, discard
from ..window import Window
from .core import StateColors, Style, UIElement

__all__ = ["Field", "FieldStyle"]


@dataclass
class FieldStyle(Style):
    """`Style` for `Field`s."""

    _: KW_ONLY

    background_color: StateColors | None = field(
        default_factory=lambda: StateColors.from_single(WHITE)
    )
    foreground_color: StateColors | None = None

    font_name: str = "Arial"
    size: int = 16

    bold: bool = False
    italic: bool = False

    def __post_init__(self) -> None:
        self.font = get_system_font(self.font_name, self.size, self.bold, self.italic)

    @override
    @classmethod
    def dark(cls) -> Self:
        return cls(background_color=StateColors.from_single(BLACK))

    @override
    @classmethod
    def high_contrast(cls) -> Self:
        return cls(background_color=StateColors.from_single(YELLOW))


class Field(UIElement[FieldStyle]):
    """Extensible, writeable `Field`. For styling, see `FieldStyle`."""

    def __init__(
        self,
        /,
        *,
        style: FieldStyle,
        text: str = "",
        frozen: bool = False,
        pos: Vector2 | None = None,
        size: Vector2 | None = None,
        window: Window | None = None,
        layer: int = 0,
    ) -> None:
        super().__init__(style=style, pos=pos, size=size, window=window, layer=layer)

        self._text = text
        self._is_selected = False

        self.frozen = frozen

        self.on_selected = Hook()
        self.on_unselected = Hook()

        self.on_text_changed = Hook[[str, str]](
            [lambda _1, _2: discard(self.on_any_change.notify())]
        )

        self.on_any_change += self._calculate_bounds

        def _set_selected(v: bool, /) -> None:
            self.is_selected = v

        self.on_downed += lambda: _set_selected(True)
        self.app.mouse.on_mouse_button_downed.add_callback(
            lambda btn: discard(btn == self.interaction_button and _set_selected(False))
        )

        self._calculate_bounds()

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, s: str) -> None:
        if self.frozen:
            raise ValueError("Cannot change a frozen Field's text.")

        self._text = s
        self.on_text_changed.notify(self._text, s)

    @property
    def is_selected(self) -> bool:
        return self._is_selected

    @is_selected.setter
    def is_selected(self, value: bool) -> None:
        self._is_selected = value

        if value:
            self.on_selected.notify()
        else:
            self.on_unselected.notify()

    @override
    def update(self) -> None:
        if self.is_selected:
            self.text += self.app.keyboard.text

    @override
    def render(self) -> None:
        self.app.window.surface.blit(self._surface, self.bounds)

    def _calculate_bounds(self) -> None:
        self._surface, bounds = self.style.font.render(
            self.text,
            self.style.background_color.calculate(element=self)
            if self.style.background_color
            else None,
            self.style.foreground_color.calculate(element=self)
            if self.style.foreground_color
            else None,
            size=self.style.size,
        )

        bounds.topleft = self._position

        self.bounds = Rect(bounds)
