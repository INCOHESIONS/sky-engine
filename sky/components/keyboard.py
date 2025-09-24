from dataclasses import dataclass
from typing import Callable, Self, override

import pygame

from ..core import Component
from ..enums import Key, State
from ..listenable import Listenable
from ..types import KeyLike
from ..utils import Vector2, get_by_attrs

__all__ = ["Keyboard"]

type _KeyListener = Callable[[Key], None]
type _StatefulKeyListener = Callable[[Key, State], None]


@dataclass
class _Keybinding:
    keys: tuple[Key, ...]
    action: Callable[[], None]
    state: State = State.downed


class Keyboard(Component):
    """Handles keyboard input."""

    def __init__(self) -> None:
        self._states: dict[Key, State] = {}
        self._text = ""

        self.on_key = Listenable[_StatefulKeyListener]()

        self.on_key_pressed = Listenable[_KeyListener]()
        self.on_key_downed = Listenable[_KeyListener]()
        self.on_key_released = Listenable[_KeyListener]()

        self._keybindings: list[_Keybinding] = []

    @property
    def states(self) -> dict[Key, State]:
        """The current state of all keys listed in the `Key` enum."""

        return self._states

    @property
    def text(self) -> str:
        """The text entered by the user this frame."""

        return self._text

    @override
    def update(self) -> None:
        _pressed = pygame.key.get_pressed()
        _downed = pygame.key.get_just_pressed()
        _released = pygame.key.get_just_released()

        for key in Key:
            state = State.from_bools(
                pressed=_pressed[key.value],
                released=_released[key.value],
                down=_downed[key.value],
            )

            if state != State.none:
                getattr(self, f"on_key_{state.name}").notify(key)

            self.on_key.notify(key, state)

            self._states[key] = state

        self._text = "".join(
            e.unicode for e in self.app.events.get_many(pygame.KEYDOWN)
        )

        for keybinding in self._keybindings:
            if all(self.get_state(key) == keybinding.state for key in keybinding.keys):
                keybinding.action()

    def add_keybinding(
        self,
        keys: KeyLike | tuple[KeyLike, ...],
        action: Callable[[], None],
        state: State = State.downed,
        /,
    ) -> Self:
        """
        Adds a keybinding.

        Parameters
        ----------
        keys: `KeyLike | tuple[KeyLike, ...]`
            The key or keys to bind the action to.
        action: `Callable[[], None]`
            The action to bind.
        state: `State`
            The state the action should be triggered in.

        Returns
        -------
        `Self`
            The keyboard, for chaining.
        """

        converted = tuple(
            map(Key.convert, (keys if isinstance(keys, tuple) else (keys,)))
        )
        self._keybindings.append(_Keybinding(converted, action, state))
        return self

    def add_keybindings(
        self,
        keybindings: dict[KeyLike | tuple[KeyLike, ...], Callable[[], None]],
        /,
    ) -> Self:
        """
        Adds multiple keybindings at once.

        Parameters
        ----------
        keybindings: `dict[KeyLike | tuple[KeyLike, ...], Callable[[], None]]`
            The keybindings to add.

        Returns
        -------
        `Self`
            The keyboard, for chaining.
        """

        for keys, action in keybindings.items():
            self.add_keybinding(keys, action)
        return self

    def remove_keybinding(self, keys: Key | tuple[Key, ...], /) -> None:
        """
        Removes a keybinding.

        Parameters
        ----------
        keys: `Key | tuple[Key, ...]`
            The key or keys used by the keybinding.

        Raises
        ------
        `ValueError`
            If no keybinding was found for the specified keys.
        """

        keybinding = get_by_attrs(
            self._keybindings, keys=keys if isinstance(keys, tuple) else (keys,)
        )

        self._keybindings.remove(keybinding)  # type: ignore

    def get_state(self, key: KeyLike, /) -> State:
        """
        Gets the state of a key.

        Parameters
        ----------
        key: `KeyLike`
            The key to get the state of.

        Returns
        -------
        `State`
            The key's state.
        """

        return self._states[Key.convert(key)]

    def set_state(self, key: KeyLike, state: State, /) -> None:
        """
        Sets the state of a key.

        Parameters
        ----------
        key: `KeyLike`
            The key to set the state of.
        state: `State`
            The state to set.
        """

        self._states[Key.convert(key)] = state

    def is_state(self, key: KeyLike, state: State, /) -> bool:
        """
        Checks if a key is in a certain state.
        State can be State.none to check if the key is not being interacted with at all.\n
        Equivalent to `self.get_state(key) == state`.

        Parameters
        ----------
        key: `KeyLike`
            The key to check.
        state: `State`
            The state to check for.

        Returns
        -------
        `bool`
            Whether the key is in the specified state.
        """

        return self.get_state(key) == state

    def is_pressed(self, key: KeyLike, /) -> bool:
        """
        Checks if a key is pressed (pressed for multiple frames).

        Parameters
        ----------
        key: `KeyLike`
            The key to check.

        Returns
        -------
        `bool`
            Whether the key is pressed.
        """

        return self.is_state(key, State.pressed)

    def is_downed(self, key: KeyLike, /) -> bool:
        """
        Checks if a key is downed (pressed on this frame).

        Parameters
        ----------
        key: `KeyLike`
            The key to check.

        Returns
        -------
        `bool`
            Whether the key is downed.
        """

        return self.is_state(key, State.downed)

    def is_released(self, key: KeyLike, /) -> bool:
        """
        Checks if a key is released (released on this frame).

        Parameters
        ----------
        key: `KeyLike`
            The key to check.

        Returns
        -------
        `bool`
            Whether the key is released.
        """

        return self.is_state(key, State.released)

    def any(self, state: State = State.none, /) -> bool:
        """
        Checks if any key is in a certain state.

        Parameters
        ----------
        state: `State`
            The state to check for.
            If no state is specified (and as such `state` is `State.none`), checks if any key is being interacted with at all, i.e., in any state.

        Returns
        -------
        `bool`
            Whether any key is in the specified state.
        """

        return any(
            self.get_state(key) == state
            if state != State.none
            else self.get_state(key) != State.none
            for key in self._states
        )

    def get_axis(
        self, neg: KeyLike, pos: KeyLike, /, *, state: State = State.pressed
    ) -> float:
        """
        Gets the axis value of a key.

        Parameters
        ----------
        neg: `KeyLike`
            The key to check for negative values.
        pos: `KeyLike`
            The key to check for positive values.
        state: `State`
            The state to check for. Cannot be `State.none`. Defaults to `State.pressed`.

        Returns
        -------
        `float`
            The axis value of the key.

        Raises
        ------
        `AssertionError`
            If `state` is `State.none`.
        """

        assert state != State.none

        return int(self.is_state(pos, state)) - int(self.is_state(neg, state))

    def get_movement(
        self,
        vertical_axis: tuple[KeyLike, KeyLike],
        horizontal_axis: tuple[KeyLike, KeyLike],
        /,
        *,
        state: State = State.pressed,
        normalize: bool = True,
    ) -> Vector2:
        """
        Two axis to use for movement.

        Parameters
        ----------
        vertical_axis: `tuple[KeyLike, KeyLike]`
            The keys to check for vertical movement.
        horizontal_axis: `tuple[KeyLike, KeyLike]`
            The keys to check for horizontal movement.
        state: `State`
            The state to check for. Cannot be `State.none`. Defaults to `State.pressed`.
        normalize: `bool`
            Whether to normalize the movement to the range [0, 1]. Defaults to `True`.

        Returns
        -------
        `Vector2`
            The movement of the keys.

        Raises
        ------
        `AssertionError`
            If `state` is `State.none`.
        """

        movement = Vector2(
            self.get_axis(*vertical_axis, state=state),
            self.get_axis(*horizontal_axis, state=state),
        )

        if normalize:
            movement.normalize()

        return movement
