from typing import override

import pygame

from ..core import Component
from ..enums import State
from ..utils import Vector2

__all__ = ["Mouse"]


class Mouse(Component):
    def __init__(self) -> None:
        self._pos = Vector2()
        self._vel = Vector2()
        self._states: list[State] = []
        self._num_buttons = 3

    @property
    def position(self) -> Vector2:
        return self._pos

    @property
    def velocity(self) -> Vector2:
        return self._vel

    @property
    def states(self) -> list[State]:
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

    def is_state(self, button: int, state: State, /) -> bool:
        return self.states[button] == state

    def is_pressed(self, button: int, /) -> bool:
        return self.is_state(button, State.pressed)

    def is_downed(self, button: int, /) -> bool:
        return self.is_state(button, State.downed)

    def is_released(self, button: int, /) -> bool:
        return self.is_state(button, State.released)

    def any(self, state: State = State.none, /) -> bool:
        return (
            any(b != State.none for b in self.states)
            if state == State.none
            else any(b == state for b in self.states)
        )
