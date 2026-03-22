from collections.abc import Mapping
from typing import TYPE_CHECKING, final, override

import pygame
from pygame.constants import MOUSEBUTTONDOWN, MOUSEBUTTONUP

from .._compat import get_mouse_position
from ..core import Cursor, InputManager, MouseButton, State
from ..hook import Hook
from ..types import CursorLike, MouseButtonLike, StateLike
from ..utils import Vector2

if TYPE_CHECKING:
    from ..window import Window


__all__ = ["Mouse"]


@final
class Mouse(InputManager):
    """Handles mouse input."""

    def __init__(self, window: Window, /) -> None:
        super().__init__(window)

        self._pos = Vector2()
        self._vel = Vector2()
        self._acc = Vector2()
        self._wheel_delta = Vector2()

        self._states = {btn.value: State.none for btn in MouseButton}

        self._setup_hooks()

        self.use_system = False
        """Whether or not to use system-level APIs to track the mouse's position. Note that its position can be negative when outside the window."""

    @property
    def position(self) -> Vector2:
        """The mouse's position."""

        return self._pos.copy()

    pos = position

    @property
    def previous_position(self) -> Vector2:
        """The mouse's previous position."""

        return self._pos - self._vel

    @property
    def velocity(self) -> Vector2:
        """The relative change in the mouse's position since the last frame."""

        return self._vel.copy()

    vel = velocity

    @property
    def acceleration(self) -> Vector2:
        """The relative change in the mouse's velocity since the last frame."""

        return self._acc.copy()

    acc = acceleration

    @property
    def wheel_delta(self) -> Vector2:
        """The change in the mouse's scroll wheel position since the last frame."""

        return self._wheel_delta.copy()

    scroll_delta = wheel_delta

    @property
    def states(self) -> Mapping[MouseButton, State]:
        """The current state of all buttons listed in the `MouseButton` enum."""

        return {MouseButton(btn): state for btn, state in self._states.items()}

    @property
    def cursor(self) -> pygame.Cursor:
        """Gets the cursor. Use set_cursor() to set the cursor."""

        return pygame.mouse.get_cursor()

    @property
    def relative_mode(self) -> bool:
        """
        Gets or sets whether the mouse is in relative mode.\n
        Effectively hides and constrains the mouse to the window, but still reports mouse movement even if the hidden mouse is at the edges of the window and not actually moving.\n
        Useful for 3D games where the player moves the camera with the mouse.

        # Getter

        Returns
        -------
        `bool`
            Whether the mouse is in relative mode.

        # Setter

        Parameters
        ----------
        enable: `bool`
            Whether to enable relative mode.
        """

        return pygame.mouse.get_relative_mode()

    @relative_mode.setter
    def relative_mode(self, enable: bool, /) -> None:
        pygame.mouse.set_relative_mode(enable)

    @override
    def update(self) -> None:
        new_pos = self._get_pos()
        new_vel = new_pos - self._pos

        self._pos = new_pos
        self._acc = new_vel - self._vel
        self._vel = new_vel

        if not self._vel.is_clear():
            self.on_mouse_move.notify()

        downed: set[int] = set(
            e.button - 1
            for e in self.app.events.get_many(MOUSEBUTTONDOWN)
            if self._window == e.window
        )
        released: set[int] = set(
            e.button - 1
            for e in self.app.events.get_many(MOUSEBUTTONUP)
            if self._window == e.window
        )

        for btn, state in self._states.items():
            self._states[btn] = (
                State.pressed
                if state is State.downed
                else State.none
                if state is State.released
                else state
            )

            if btn in downed:
                self._states[btn] = State.downed

            if btn in released:
                self._states[btn] = State.released

            new_state = self._states[btn]

            if new_state != State.none:
                getattr(self, f"on_mouse_button_{new_state.name}").notify(
                    MouseButton(btn)
                )

            if state != State.none:
                self.on_mouse_button.notify(MouseButton(btn), new_state)

        self._wheel_delta = sum(
            map(
                lambda e: Vector2(e.precise_x, e.precise_y),
                self.app.events.get_many(pygame.MOUSEWHEEL),
            ),
            Vector2(),
        )

        if not self._wheel_delta.is_clear():
            self.on_mouse_wheel.notify(self._wheel_delta)

    def get_state(self, button: MouseButtonLike, /) -> State:
        """
        Gets the state of a button.

        Parameters
        ----------
        button: `MouseButtonLike`
            The button to get the state of.

        Returns
        -------
        `State`
            The button's state.
        """

        return self._states[MouseButton.convert(button).value]

    def set_state(self, button: MouseButtonLike, /, *, state: StateLike) -> None:
        """
        Sets the state of a button.

        Parameters
        ----------
        button: `MouseButtonLike`
            The button to set the state of.
        state: `StateLike`
            The state to set.
        """

        self._states[MouseButton.convert(button).value] = State.convert(state)

    def is_state(self, button: MouseButtonLike, state: StateLike, /) -> bool:
        """
        Checks if a button is in a certain state.
        State can be `State.none` to check if the button is not being interacted with at all.\n
        Equivalent to `self.get_state(button) == state`.

        Parameters
        ----------
        button: MouseButtonLike
            The button to check.
        state: `StateLike`
            The state to check for.

        Returns
        -------
        `bool`
            Whether the button is in the specified state.
        """
        return self.get_state(button) == State.convert(state)

    def is_pressed(self, button: MouseButtonLike, /) -> bool:
        """
        Checks if a button is pressed (pressed for multiple frames).

        Parameters
        ----------
        button: `MouseButtonLike`
            The button to check.

        Returns
        -------
        `bool`
            Whether the button is pressed.
        """
        return self.is_state(button, State.pressed)

    def is_downed(self, button: MouseButtonLike, /) -> bool:
        """
        Checks if a button is downed (pressed on this frame).

        Parameters
        ----------
        button: `MouseButtonLike`
            The button to check.

        Returns
        -------
        `bool`
            Whether the button is downed.
        """
        return self.is_state(button, State.downed)

    def is_released(self, button: MouseButtonLike, /) -> bool:
        """
        Checks if a button is released (released on this frame).

        Parameters
        ----------
        button: `MouseButtonLike`
            The button to check.

        Returns
        -------
        `bool`
            Whether the button is released.
        """
        return self.is_state(button, State.released)

    def any(self, state: StateLike = State.none, /) -> bool:
        """
        Checks if any button is in a certain state.

        Parameters
        ----------
        state: `StateLike`
            The state to check for.
            If no state is specified (and as such `state` is `State.none`), checks if any button is being interacted with at all, i.e., in any state.

        Returns
        -------
        `bool`
            Whether any button is in the specified state.
        """

        state = State.convert(state)

        return (
            any(b != State.none for b in self.states)
            if state == State.none
            else any(b == state for b in self.states)
        )

    def set_cursor(self, cursor: CursorLike, /) -> None:
        pygame.mouse.set_cursor(Cursor.as_cursor(cursor))

    def _setup_hooks(self) -> None:
        self.on_mouse_button = Hook[[MouseButton, State]]()
        """Executes whenever the state of any mouse button changes, including changes to `State.none`"""

        self.on_mouse_button_pressed = Hook[[MouseButton]]()
        """Executes whenever the state of any mouse button changes `State.pressed`"""

        self.on_mouse_button_downed = Hook[[MouseButton]]()
        """Executes whenever the state of any mouse button changes `State.downed`"""

        self.on_mouse_button_released = Hook[[MouseButton]]()
        """Executes whenever the state of any mouse button changes `State.released`"""

        self.on_mouse_wheel = Hook[[Vector2]]()
        """Executes whenever the mouse wheel is scrolled. Inputs on the x-axis happen when the wheel is scrolled while shift is being pressed."""

        self.on_scroll = self.on_mouse_wheel  # alias

        self.on_mouse_move = Hook()
        """Executes whenever the mouse's velocity is different from zero."""

    def _get_pos(self) -> Vector2:
        return Vector2(
            get_mouse_position() - self.app.window.position
            if self.use_system
            else pygame.mouse.get_pos()
        )
