"""Contains the `Mouse` component that handles mouse input."""

from collections.abc import Sequence
from typing import final, override

import pygame

from ..core import Cursor, MouseButton, Service, State
from ..hook import Hook
from ..types import CursorLike, MouseButtonLike, StateLike
from ..utils import Vector2

__all__ = ["Mouse"]


@final
class Mouse(Service):
    """Handles mouse input."""

    def __init__(self) -> None:
        self._pos = Vector2()
        self._vel = Vector2()
        self._acc = Vector2()
        self._wheel_delta = Vector2()

        self._num_buttons = len(MouseButton)

        self._states = [State.none for _ in range(self._num_buttons)]

        self.on_mouse_button = Hook[[MouseButton, State]]()

        self.on_mouse_button_pressed = Hook[[MouseButton]]()
        self.on_mouse_button_downed = Hook[[MouseButton]]()
        self.on_mouse_button_released = Hook[[MouseButton]]()

        self.on_mouse_wheel = Hook[[Vector2]]()
        self.on_scroll = self.on_mouse_wheel

        self.on_mouse_move = Hook()

    @property
    def position(self) -> Vector2:
        """The mouse's position, in pixel coordinates."""

        return self._pos.copy()

    pos = position

    @property
    def velocity(self) -> Vector2:
        """The relative change in the mouse's position since the last frame, in pixel coordinates."""

        return self._vel.copy()

    vel = velocity

    @property
    def acceleration(self) -> Vector2:
        """The relative change in the mouse's velocity since the last frame, in pixel coordinates."""

        return self._acc.copy()

    acc = acceleration

    @property
    def wheel_delta(self) -> Vector2:
        """The change in the mouse's scroll wheel position since the last frame."""

        return self._wheel_delta.copy()

    scroll_delta = wheel_delta

    @property
    def states(self) -> Sequence[State]:
        """The current state of all buttons listed in the `MouseButton` enum."""

        return self._states.copy()

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
        self._pos = Vector2(pygame.mouse.get_pos())
        new_vel = Vector2(pygame.mouse.get_rel())
        self._acc = new_vel - self._vel
        self._vel = new_vel

        if not self._vel.is_clear():
            self.on_mouse_move.notify()

        _pressed = pygame.mouse.get_pressed()
        _downed = pygame.mouse.get_just_pressed()
        _released = pygame.mouse.get_just_released()

        self._states = [
            State.from_bools(
                pressed=_pressed[i],
                released=_released[i],
                down=_downed[i],
            )
            for i in range(self._num_buttons)
        ]

        for button, state in zip(MouseButton, self._states):
            if state != State.none:
                self.on_mouse_button.notify(button, state)
                getattr(self, f"on_mouse_button_{state.name}").notify(button)

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
