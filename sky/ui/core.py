"""Core UI functionality."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Self, final

from ..colors import DARK_GRAY, LIGHT_GRAY, WHITE
from ..core import MouseButton, State
from ..hook import Hook
from ..utils import Color, Rect, Vector2
from ..window import Window

if TYPE_CHECKING:
    from ..app import App

__all__ = [
    "StateColors",
    "Style",
    "UIElement",
]


class UIElement[TStyle: Style = Any](ABC):
    """Base class for `UI` elements."""

    app: ClassVar[App] = None  # pyright: ignore[reportAssignmentType]

    def __init__(
        self,
        /,
        *,
        style: TStyle,
        pos: Vector2 | None = None,
        size: Vector2 | None = None,
        window: Window | None = None,
        layer: int = 0,
    ) -> None:
        self._position = pos or Vector2()
        self._size = size or Vector2()
        self._window = window or self.app.window

        self._state = State.none
        self._enabled = True
        self._style = style

        self.interaction_button = MouseButton.left
        """The button used to interact with the element."""

        self.layer = layer
        """The layer on which the element is rendered. Used for sorting elements in the UI."""

        self.on_enabled = Hook()
        """Notified when the element is enabled."""

        self.on_disabled = Hook()
        """Notified when the element is disabled."""

        self.on_downed = Hook()
        """Notified when the element's state changes to `State.downed`."""

        self.on_pressed = Hook()
        """Notified when the element's state changes to `State.pressed`."""

        self.on_released = Hook()
        """Notified when the element's state changes to `State.released`."""

        self.on_state_changed = Hook[[State, State]]()
        """Listens to changes to the element's state."""

        self.on_position_changed = Hook[[Vector2, Vector2]]()
        """Listens for changes to the element's position, providing the old and new values."""

        self.on_size_changed = Hook[[Vector2, Vector2]]()
        """Listens for changes to the element's size, providing the old and new values."""

        self.on_style_changed = Hook[[TStyle, TStyle]]()
        """Listens for changes to the element's style, providing the old and new values."""

        self.on_any_change = Hook()  # type: Hook  # pyright: ignore[reportTypeCommentUsage]  # HACK:
        """Listens to `on_state_changed`, `on_position_changed`, `on_size_changed` and `on_style_changed`."""

        def __add(_1: Any, _2: Any):
            self.on_any_change.notify()

        self.on_state_changed += __add
        self.on_position_changed += __add
        self.on_size_changed += __add
        self.on_style_changed += __add

    @final
    @property
    def position(self) -> Vector2:
        """The element's position. Changing it will notify `self.on_position_changed`."""

        return self._position

    @position.setter
    def position(self, value: Vector2, /) -> None:
        if self._position != value:
            self.on_position_changed.notify(self._position, value)

        self._position = value

    @final
    @property
    def size(self) -> Vector2:
        """The element's size. Changing it will notify `self.on_size_changed`."""

        return self._size

    @size.setter
    def size(self, value: Vector2, /) -> None:
        if self._size != value:
            self.on_size_changed.notify(self._size, value)

        self._size = value

    @property
    def bounds(self) -> Rect:
        """The bounds of this element."""

        return Rect(self._position, self._size)

    @bounds.setter
    def bounds(self, value: Rect, /) -> None:
        self._position = Vector2(value.topleft)
        self._size = Vector2(value.size)

    @final
    @property
    def style(self) -> TStyle:
        """The element's style. Changing it will notify `self.on_style_changed`."""

        return self._style

    @style.setter
    def style(self, value: TStyle, /) -> None:
        if self._style != value:
            self.on_style_changed.notify(self._style, value)

        self._style = value

    @final
    @property
    def enabled(self) -> bool:
        """Whether or not this element is enabled. Enabling or disabling it will notify `self.on_enabled` or `self.on_disabled`."""

        return self._enabled

    @enabled.setter
    def enabled(self, value: bool, /) -> None:
        if self._enabled != value:
            if self._enabled:
                self.on_enabled.notify()
            else:
                self.on_disabled.notify()

        self._enabled = value

    @property
    def disabled(self) -> bool:
        """Whether or not this element is disabled. Enabling or disabling it will notify `self.on_enabled` or `self.on_disabled`."""

        return not self._enabled

    @disabled.setter
    def disabled(self, value: bool, /) -> None:
        self.enabled = not value

    @property
    def state(self) -> State:
        """The element's state."""

        return self._state

    @property
    def window(self) -> Window:
        """The window this element is in."""

        return self._window

    # TODO: caching
    @property
    def is_mouse_inside(self) -> bool:
        """Whether or not the mouse is inside this element's bounds."""

        return self.bounds.collidepoint(self.app.mouse.position)

    @final
    def toggle(self) -> None:
        """Toggles whether or not this element is enabled."""

        self._enabled = not self._enabled

    def calculate_state(self) -> State:
        if self.app.ui.interacting is not None:
            new_state = State.none
        else:
            mouse_state = self.app.mouse.get_state(self.interaction_button)

            new_state = (
                mouse_state
                if self.is_mouse_inside
                else self._state
                if mouse_state in (State.downed, State.pressed)
                else State.none
            )

        if self._state != new_state:
            self.on_state_changed.notify(self._state, new_state)

        self._state = new_state

        if self._state is not State.none:
            getattr(self, f"on_{self._state.name.lower()}").notify()

        return self._state

    def update(self) -> None: ...

    @abstractmethod
    def render(self) -> None:
        raise NotImplementedError()


@final
@dataclass(slots=True, frozen=True)
class StateColors:
    """Colors for different states of UI elements."""

    _: KW_ONLY

    # TODO: change values
    normal_color: Color = field(default_factory=lambda: WHITE)
    hovered_color: Color = field(default_factory=lambda: LIGHT_GRAY)
    downed_color: Color = field(default_factory=lambda: DARK_GRAY)
    pressed_color: Color = field(default_factory=lambda: DARK_GRAY)
    released_color: Color = field(default_factory=lambda: WHITE)
    disabled_color: Color = field(default_factory=lambda: WHITE.with_opacity(0.5))

    @classmethod
    def from_single(cls, color: Color, /) -> Self:
        return cls(
            normal_color=color,
            hovered_color=color,
            downed_color=color,
            pressed_color=color,
            released_color=color,
            disabled_color=color,
        )

    def calculate(self, /, *, element: UIElement) -> Color:
        if element.disabled:
            return self.disabled_color

        if element.state == State.none:
            return self.hovered_color if element.is_mouse_inside else self.normal_color

        return getattr(self, element.state.name + "_color")


# all values should have defaults; defaults should be fit for a white theme
class Style(ABC):
    """Base class for UI styles."""

    @final
    @classmethod
    def white(cls) -> Self:
        return cls()

    @classmethod
    @abstractmethod
    def dark(cls) -> Self:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def high_contrast(cls) -> Self:
        raise NotImplementedError()
