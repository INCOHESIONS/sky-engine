"""All of the engine's most important enums. Mostly input-related."""

from __future__ import annotations

from enum import Enum, IntEnum, auto
from typing import Self, final

import pygame

from .types import CursorLike

__all__ = [
    "Cursor",
    "InputEnum",
    "Key",
    "MouseButton",
    "State",
]


class InputEnum(IntEnum):
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
class MouseButton(InputEnum):
    """Mouse button enum."""

    left = 0
    middle = auto()
    right = auto()


@final
class Key(InputEnum):
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
    break_ = pygame.K_BREAK
    capslock = pygame.K_CAPSLOCK
    caret = pygame.K_CARET
    clear = pygame.K_CLEAR
    colon = pygame.K_COLON
    comma = pygame.K_COMMA
    currency_subunit = pygame.K_CURRENCYSUBUNIT
    currency_unit = pygame.K_CURRENCYUNIT
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
    keypad0 = pygame.K_KP0  # what's the difference between these (↓) two?
    keypad1 = pygame.K_KP1
    keypad2 = pygame.K_KP2
    keypad3 = pygame.K_KP3
    keypad4 = pygame.K_KP4
    keypad5 = pygame.K_KP5
    keypad6 = pygame.K_KP6
    keypad7 = pygame.K_KP7
    keypad8 = pygame.K_KP8
    keypad9 = pygame.K_KP9
    keypad_0 = pygame.K_KP_0  # what's the difference between these (↑) two?
    keypad_1 = pygame.K_KP_1
    keypad_2 = pygame.K_KP_2
    keypad_3 = pygame.K_KP_3
    keypad_4 = pygame.K_KP_4
    keypad_5 = pygame.K_KP_5
    keypad_6 = pygame.K_KP_6
    keypad_7 = pygame.K_KP_7
    keypad_8 = pygame.K_KP_8
    keypad_9 = pygame.K_KP_9
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
    left_ctrl = pygame.K_LCTRL
    left_gui = pygame.K_LGUI
    left_meta = pygame.K_LMETA
    left_parenthesis = pygame.K_LEFTPAREN
    left_shift = pygame.K_LSHIFT
    left_super = pygame.K_LSUPER
    less = pygame.K_LESS
    menu = pygame.K_MENU
    minus = pygame.K_MINUS
    mode = pygame.K_MODE
    numlock = pygame.K_NUMLOCK
    numlock_clear = pygame.K_NUMLOCKCLEAR
    page_down = pygame.K_PAGEDOWN
    page_up = pygame.K_PAGEUP
    pause = pygame.K_PAUSE
    percent = pygame.K_PERCENT
    period = pygame.K_PERIOD
    plus = pygame.K_PLUS
    power = pygame.K_POWER
    print = pygame.K_PRINT
    printscreen = pygame.K_PRINTSCREEN
    question = pygame.K_QUESTION
    quote = pygame.K_QUOTE
    quotedbl = pygame.K_QUOTEDBL
    return_ = pygame.K_RETURN
    right = pygame.K_RIGHT
    right_alt = pygame.K_RALT
    right_bracket = pygame.K_RIGHTBRACKET
    right_control = pygame.K_RCTRL
    right_ctrl = pygame.K_RCTRL
    right_gui = pygame.K_RGUI
    right_meta = pygame.K_RMETA
    right_parenthesis = pygame.K_RIGHTPAREN
    right_shift = pygame.K_RSHIFT
    right_super = pygame.K_RSUPER
    scrolllock = pygame.K_SCROLLLOCK
    scrollock = pygame.K_SCROLLOCK
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
    ç = 231
    _ = 180
    tilde = 126


@final
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
        if down:
            return State.downed
        if released:
            return State.released
        if pressed:
            return State.pressed
        return State.none


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
