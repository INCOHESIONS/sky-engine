from typing import override

import pygame

from ..core import Component
from ..enums import State
from ..utils import Vector2

__all__ = ["Mouse"]


class Mouse(Component):
    """Handles mouse input."""

    def __init__(self) -> None:
        self._pos = Vector2()
        self._vel = Vector2()
        self._states: list[State] = []
        self._num_buttons = 3

    @property
    def position(self) -> Vector2:
        """The mouse's position, in pixel coordinates."""

        return self._pos

    @property
    def velocity(self) -> Vector2:
        """The relative change in the mouse's position since the last frame, in pixel coordinates."""

        return self._vel

    @property
    def states(self) -> list[State]:
        """The current state of all buttons listed in the `MouseButton` enum."""

        return self._states

    @override
    def update(self) -> None:
        self._pos = Vector2(pygame.mouse.get_pos())
        self._vel = Vector2(pygame.mouse.get_rel())

        _pressed = pygame.mouse.get_pressed()
        _downed = pygame.mouse.get_just_pressed()
        _released = pygame.mouse.get_just_released()

        self._states = [
            State.from_bools(
                pressed=_pressed[i],
                released=_released[i],
                down=_downed[i],
            )
            for i in range(0, self._num_buttons)
        ]

    def get_state(self, button: int, /) -> State:
        """
        Gets the state of a button.

        Parameters
        ----------
        button: int
            The button to get the state of.

        Returns
        -------
        State
            The button's state.
        """

        return self._states[button]

    def is_state(self, button: int, state: State, /) -> bool:
        """
        Checks if a button is in a certain state.
        State can be State.none to check if the button is not being interacted with at all.\n
        Equivalent to `self.get_state(button) == state`.

        Parameters
        ----------
        button: int
            The button to check.
        state: State
            The state to check for.

        Returns
        -------
        bool
            Whether the button is in the specified state.
        """
        return self.get_state(button) == state

    def is_pressed(self, button: int, /) -> bool:
        """
        Checks if a button is pressed (pressed for multiple frames).

        Parameters
        ----------
        button: int
            The button to check.

        Returns
        -------
        bool
            Whether the button is pressed.
        """
        return self.is_state(button, State.pressed)

    def is_downed(self, button: int, /) -> bool:
        """
        Checks if a button is downed (pressed on this frame).

        Parameters
        ----------
        button: int
            The button to check.

        Returns
        -------
        bool
            Whether the button is downed.
        """
        return self.is_state(button, State.downed)

    def is_released(self, button: int, /) -> bool:
        """
        Checks if a button is released (released on this frame).

        Parameters
        ----------
        button: int
            The button to check.

        Returns
        -------
        bool
            Whether the button is released.
        """
        return self.is_state(button, State.released)

    def any(self, state: State = State.none, /) -> bool:
        """
        Checks if any button is in a certain state.

        Parameters
        ----------
        state: State
            The state to check for.
            If no state is specified (and as such `state` is `State.none`), checks if any button is being interacted with at all, i.e., in any state.

        Returns
        -------
        bool
            Whether any button is in the specified state.
        """
        return (
            any(b != State.none for b in self.states)
            if state == State.none
            else any(b == state for b in self.states)
        )
