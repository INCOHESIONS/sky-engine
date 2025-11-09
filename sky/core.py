"""Core engine functionality, including most input-related types."""

from __future__ import annotations

from abc import ABC
from collections.abc import Iterator
from dataclasses import KW_ONLY, dataclass, field
from enum import Enum, IntEnum, auto, unique
from typing import TYPE_CHECKING, Callable, ClassVar, Self, final

import pygame
from screeninfo import Monitor as ScreenInfoMonitor

from .hook import Hook
from .types import Coroutine, CursorLike, KeyLike, ModifierLike, StateLike
from .utils import Vector2

if TYPE_CHECKING:
    from .app import App

__all__ = [
    "Component",
    "Cursor",
    "Key",
    "Keybinding",
    "Modifier",
    "Monitor",
    "MouseButton",
    "State",
]


class Component(ABC):
    """Base class for components."""

    app: ClassVar[App] = None  # pyright: ignore[reportAssignmentType]

    def start(self) -> Coroutine | None:
        """Runs before the first frame, after `entrypoint` and before `setup`. Can be a Coroutine."""

    def stop(self) -> Coroutine | None:
        """Runs after the last frame, after `teardown` and before `cleanup`. Can be a Coroutine."""

    def update(self) -> None:
        """Runs every frame, after `pre_update` and before `post_update`."""


class Service(Component, ABC):
    """Services are global components that work across `Scene`s."""


@final
@dataclass(slots=True, frozen=True)
class Monitor:
    """Stores information about a monitor. Basically `screeninfo.Monitor` but with some extra information."""

    name: str
    position: Vector2
    size: Vector2
    is_primary: bool
    index: int

    @classmethod
    def from_monitor(cls, monitor: ScreenInfoMonitor, /, *, index: int) -> Self:
        """Creates a `Monitor` object from a `screeninfo.Monitor` object."""

        return cls(
            monitor.name or "Unnamed Monitor",
            Vector2(monitor.x, monitor.y),
            Vector2(monitor.width, monitor.height),
            monitor.is_primary or index == 0,
            index,
        )

    @property
    def refresh_rate(self) -> int:
        """The refresh rate of the monitor. Returns -1 if pygame's video system hasn't been initialized (i.e. `pygame.init()` hasn't been called)."""

        try:
            return pygame.display.get_desktop_refresh_rates()[self.index]
        except pygame.error:
            return -1


class _InputEnum(IntEnum):
    """Base class for input-related enums."""

    @final
    @classmethod
    def convert(cls, value: Self | str | int, /) -> Self:
        """
        Converts a `str` or an `int` to their equilavent `Enum` instances.
        If the value happens to already be an `Enum`, simply return it, ensuring
        that all valid values passed into this classmethod return an `Enum` instance.

        Parameters
        ----------
        value : `Self | str | int`
            The value to be converted.

        Returns
        -------
        `Self`
            The converted `Enum` instance.

        Raises
        ------
        `ValueError`
            If the value is not among the values defined.

        `KeyError`
            If the value is not among the keys defined.
        """

        return cls(value) if isinstance(value, int) else cls[value.lower()]


@final
@unique
class MouseButton(_InputEnum):
    """Mouse button enum."""

    left = 0
    middle = auto()
    right = auto()


@final
class Key(_InputEnum):
    """Key enum."""

    alpha_0 = pygame.K_0
    alpha_1 = pygame.K_1
    alpha_2 = pygame.K_2
    alpha_3 = pygame.K_3
    alpha_4 = pygame.K_4
    alpha_5 = pygame.K_5
    alpha_6 = pygame.K_6
    alpha_7 = pygame.K_7
    alpha_8 = pygame.K_8
    alpha_9 = pygame.K_9
    ac_back = pygame.K_AC_BACK
    ampersand = pygame.K_AMPERSAND
    asterisk = pygame.K_ASTERISK
    at = pygame.K_AT
    backquote = pygame.K_BACKQUOTE
    backslash = pygame.K_BACKSLASH
    backspace = pygame.K_BACKSPACE
    break_ = pygame.K_BREAK  # alias to pause
    capslock = pygame.K_CAPSLOCK
    caret = pygame.K_CARET
    clear = pygame.K_CLEAR
    colon = pygame.K_COLON
    comma = pygame.K_COMMA
    currency_subunit = pygame.K_CURRENCYSUBUNIT
    currency_unit = pygame.K_CURRENCYUNIT  # alias to euro
    delete = pygame.K_DELETE
    dollar = pygame.K_DOLLAR
    down = pygame.K_DOWN
    end = pygame.K_END
    equals = pygame.K_EQUALS
    escape = pygame.K_ESCAPE
    euro = pygame.K_EURO
    exclaim = pygame.K_EXCLAIM
    f1 = pygame.K_F1
    f2 = pygame.K_F2
    f3 = pygame.K_F3
    f4 = pygame.K_F4
    f5 = pygame.K_F5
    f6 = pygame.K_F6
    f7 = pygame.K_F7
    f8 = pygame.K_F8
    f9 = pygame.K_F9
    f10 = pygame.K_F10
    f11 = pygame.K_F11
    f12 = pygame.K_F12
    f13 = pygame.K_F13
    f14 = pygame.K_F14
    f15 = pygame.K_F15
    greater = pygame.K_GREATER
    hash = pygame.K_HASH
    help = pygame.K_HELP
    home = pygame.K_HOME
    insert = pygame.K_INSERT
    keypad0 = pygame.K_KP0
    keypad1 = pygame.K_KP1
    keypad2 = pygame.K_KP2
    keypad3 = pygame.K_KP3
    keypad4 = pygame.K_KP4
    keypad5 = pygame.K_KP5
    keypad6 = pygame.K_KP6
    keypad7 = pygame.K_KP7
    keypad8 = pygame.K_KP8
    keypad9 = pygame.K_KP9
    keypad_0 = pygame.K_KP_0  # alias to keypad0
    keypad_1 = pygame.K_KP_1  # alias to keypad1
    keypad_2 = pygame.K_KP_2  # alias to keypad2
    keypad_3 = pygame.K_KP_3  # alias to keypad3
    keypad_4 = pygame.K_KP_4  # alias to keypad4
    keypad_5 = pygame.K_KP_5  # alias to keypad5
    keypad_6 = pygame.K_KP_6  # alias to keypad6
    keypad_7 = pygame.K_KP_7  # alias to keypad7
    keypad_8 = pygame.K_KP_8  # alias to keypad8
    keypad_9 = pygame.K_KP_9  # alias to keypad9
    keypad_divide = pygame.K_KP_DIVIDE
    keypad_enter = pygame.K_KP_ENTER
    keypad_equals = pygame.K_KP_EQUALS
    keypad_minus = pygame.K_KP_MINUS
    keypad_multiply = pygame.K_KP_MULTIPLY
    keypad_period = pygame.K_KP_PERIOD
    keypad_plus = pygame.K_KP_PLUS
    left = pygame.K_LEFT
    left_alt = pygame.K_LALT
    left_bracket = pygame.K_LEFTBRACKET
    left_control = pygame.K_LCTRL
    left_ctrl = pygame.K_LCTRL  # alias to left_control
    left_gui = pygame.K_LGUI
    left_meta = pygame.K_LMETA  # alias to left_gui
    left_parenthesis = pygame.K_LEFTPAREN
    left_shift = pygame.K_LSHIFT
    left_super = pygame.K_LSUPER  # alias to left_gui
    less = pygame.K_LESS
    menu = pygame.K_MENU
    minus = pygame.K_MINUS
    mode = pygame.K_MODE
    numlock = pygame.K_NUMLOCK
    numlock_clear = pygame.K_NUMLOCKCLEAR  # alias to numlock
    page_down = pygame.K_PAGEDOWN
    page_up = pygame.K_PAGEUP
    pause = pygame.K_PAUSE
    percent = pygame.K_PERCENT
    period = pygame.K_PERIOD
    plus = pygame.K_PLUS
    power = pygame.K_POWER
    print = pygame.K_PRINT
    printscreen = pygame.K_PRINTSCREEN  # alias to print
    question = pygame.K_QUESTION
    quote = pygame.K_QUOTE
    quotedbl = pygame.K_QUOTEDBL
    return_ = pygame.K_RETURN
    right = pygame.K_RIGHT
    right_alt = pygame.K_RALT
    right_bracket = pygame.K_RIGHTBRACKET
    right_control = pygame.K_RCTRL
    right_ctrl = pygame.K_RCTRL  # alias to right_control
    right_gui = pygame.K_RGUI
    right_meta = pygame.K_RMETA  # alias to right_gui
    right_parenthesis = pygame.K_RIGHTPAREN
    right_shift = pygame.K_RSHIFT
    right_super = pygame.K_RSUPER  # alias to right_gui
    scrolllock = pygame.K_SCROLLLOCK
    scrollock = pygame.K_SCROLLOCK  # alias to scrolllock
    semicolon = pygame.K_SEMICOLON
    slash = pygame.K_SLASH
    space = pygame.K_SPACE
    sysreq = pygame.K_SYSREQ
    tab = pygame.K_TAB
    underscore = pygame.K_UNDERSCORE
    unknown = pygame.K_UNKNOWN
    up = pygame.K_UP
    a = pygame.K_a
    b = pygame.K_b
    c = pygame.K_c
    d = pygame.K_d
    e = pygame.K_e
    f = pygame.K_f
    g = pygame.K_g
    h = pygame.K_h
    i = pygame.K_i
    j = pygame.K_j
    k = pygame.K_k
    l = pygame.K_l  # noqa: E741
    m = pygame.K_m
    n = pygame.K_n
    o = pygame.K_o
    p = pygame.K_p
    q = pygame.K_q
    r = pygame.K_r
    s = pygame.K_s
    t = pygame.K_t
    u = pygame.K_u
    v = pygame.K_v
    w = pygame.K_w
    x = pygame.K_x
    y = pygame.K_y
    z = pygame.K_z

    pre_accent = 180  # keycode for before an accent is inputted
    tilde = 126
    ç = 231

    _ = underscore  # alias


_mod_to_key = {
    pygame.KMOD_LSHIFT: Key.left_shift,
    pygame.KMOD_RSHIFT: Key.right_shift,
    pygame.KMOD_LCTRL: Key.left_ctrl,
    pygame.KMOD_RCTRL: Key.right_ctrl,
    pygame.KMOD_LALT: Key.left_alt,
    pygame.KMOD_RALT: Key.right_alt,
    pygame.KMOD_LMETA: Key.left_meta,
    pygame.KMOD_RMETA: Key.right_meta,
    pygame.KMOD_CAPS: Key.capslock,
    pygame.KMOD_NUM: Key.numlock,
    pygame.KMOD_MODE: Key.mode,
}


@final
@unique
class Modifier(IntEnum):
    """Modifier keys."""

    left_shift = Key.left_shift
    right_shift = Key.right_shift
    left_ctrl = Key.left_ctrl
    right_ctrl = Key.right_ctrl
    left_alt = Key.left_alt
    right_alt = Key.right_alt
    left_meta = Key.left_meta
    right_meta = Key.right_meta
    capslock = Key.capslock
    numlock = Key.numlock
    mode = Key.mode

    @classmethod
    def convert(cls, value: ModifierLike, /) -> Self:
        """
        Converts a `ModifierLike` value to a Modifier.\n
        `Key`s, `Modifier`s, `Modifier` names and key values from `pygame.locals` such as `pygame.K_LSHIFT` or modifier values such as `pygame.KMOD_LSHIFT` can be used.

        Parameters
        ----------
        value : `ModifierLike`
            The value to convert.

        Returns
        -------
        `Modifier`
            The converted modifier.

        Raises
        ------
        `ValueError`
            If the value is not among the values defined.

        `KeyError`
            If the value is not among the keys defined.
        """
        if isinstance(value, str):
            return cls[value.lower()]

        try:
            return cls(value)
        except ValueError:
            return cls(_mod_to_key[value])


@final
@unique
class State(Enum):
    """
    State of a key or button.\n
    Do not confuse `State.pressed` with `State.downed`. `State.pressed` means the key has been pressed for one or more frames, while `State.downed` means the key has just been pressed.
    """

    pressed = auto()
    downed = auto()
    released = auto()
    none = auto()

    @classmethod
    def from_bools(cls, *, pressed: bool, released: bool, down: bool) -> State:
        """
        Create a state from a set of boolean flags.

        Parameters
        ----------
            pressed: `bool`
                Whether the key is currently pressed.
            released: `bool`
                Whether the key has been released.
            down: `bool`
                Whether the key is currently down.

        Returns
        -------
            State: The state of the key.
        """

        if down:
            return State.downed
        if pressed:
            return State.pressed
        if released:
            return State.released
        return State.none

    @classmethod
    def convert(cls, value: StateLike, /) -> Self:
        return cls[value] if isinstance(value, str) else value  # pyright: ignore[reportReturnType]


@final
@dataclass(slots=True)
class Keybinding:
    """Defines a keybinding."""

    _: KW_ONLY

    keymap: dict[Key, State]

    on_activation: Hook = field(default_factory=Hook[[]])
    on_deactivation: Hook = field(default_factory=Hook[[]])

    def __post_init__(self):
        if not self.keymap:
            raise ValueError("Keybinding must have at least one key")

    def __iter__(self) -> Iterator[tuple[Key, State]]:
        return iter(self.keymap.items())

    @classmethod
    def make(
        cls,
        key: KeyLike,
        /,
        *,
        action: Callable[[], None],
        modifier: ModifierLike | None = None,
        state: State = State.downed,
    ) -> Self:
        """
        Helper method to create a keybinding.

        Parameters
        ----------
        key : `Key`
            The key to bind.
        action : `Callable[[], None]`
            The action to perform when the keybinding is activated.
        modifier : `Modifier | None`, optional
            A `Modifier` key whose state has to be `State.pressed` for the keybinding to activate.\n
            Useful for keybindings like CTRL + C, for example.
        state : `State`, optional
            The state of the key. `State.downed` by default.

        Returns
        -------
        `Self`
            The created keybinding.
        """

        key = Key.convert(key)

        if modifier is not None:
            return cls(
                keymap={Modifier.convert(modifier).value: State.pressed, key: state},
                on_activation=Hook([action]),
            )

        return cls(keymap={key: state}, on_activation=Hook([action]))


@final
class Cursor(Enum):
    """Utility for accessing system cursors."""

    hand = pygame.SYSTEM_CURSOR_HAND
    arrow = pygame.SYSTEM_CURSOR_ARROW
    ibeam = pygame.SYSTEM_CURSOR_IBEAM
    crosshair = pygame.SYSTEM_CURSOR_CROSSHAIR
    wait = pygame.SYSTEM_CURSOR_WAIT
    size_nw_se = pygame.SYSTEM_CURSOR_SIZENWSE
    size_ne_sw = pygame.SYSTEM_CURSOR_SIZENESW
    size_ns = pygame.SYSTEM_CURSOR_SIZENS
    size_we = pygame.SYSTEM_CURSOR_SIZEWE
    size_all = pygame.SYSTEM_CURSOR_SIZEALL
    no = pygame.SYSTEM_CURSOR_NO

    default = arrow  # alias
    text = ibeam  # alias
    deny = no  # alias

    @staticmethod
    def as_cursor(value: CursorLike, /) -> pygame.Cursor:
        """
        Converts a `CursorLike` value to a `pygame.Cursor`.

        Parameters
        ----------
        value: `CursorLike`
            The cursor-like value to convert.

        Returns
        -------
        `pygame.Cursor`
            The converted pygame Cursor.
        """

        return (
            value
            if isinstance(value, pygame.Cursor)
            else pygame.Cursor(
                value
                if isinstance(value, int)
                else Cursor[value.lower()].value
                if isinstance(value, str)
                else value.value
            )
        )
