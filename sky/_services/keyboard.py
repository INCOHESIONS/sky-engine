"""Contains the `Keyboard` component that handles keyboard input."""

from collections.abc import Sequence
from typing import Callable, Literal, final, override

import pygame

from ..core import Key, Keybinding, Service, State
from ..hook import Hook
from ..types import KeyLike, StateLike
from ..utils import Vector2, Vector3

__all__ = ["Keyboard"]


@final
class Keyboard(Service):
    """Handles keyboard input."""

    def __init__(self) -> None:
        self._states: dict[Key, State] = {key: State.none for key in Key}
        self._text = ""

        self._keybindings: list[Keybinding] = []
        self._active_keybindings: list[Keybinding] = []

        self.on_key = Hook[[Key, State]]()

        self.on_key_pressed = Hook[[Key]]()
        self.on_key_downed = Hook[[Key]]()
        self.on_key_released = Hook[[Key]]()

    @property
    def states(self) -> dict[Key, State]:
        """The current state of all keys listed in the `Key` enum."""

        return self._states

    @property
    def text(self) -> str:
        """The text entered by the user this frame."""

        return self._text

    @property
    def keybindings(self) -> Sequence[Keybinding]:
        """All registered keybindings."""

        return self._keybindings.copy()

    @property
    def active_keybindings(self) -> Sequence[Keybinding]:
        """All currently active keybindings."""

        return self._active_keybindings.copy()

    @override
    def update(self) -> None:
        previously_active_keybindings = self._active_keybindings.copy()

        self._active_keybindings.clear()

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
            if self.is_active(keybinding):
                keybinding.on_activation.notify()
                self._active_keybindings.append(keybinding)
            elif keybinding in previously_active_keybindings:
                keybinding.on_deactivation.notify()

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

    def set_state(self, key: KeyLike, /, *, state: StateLike) -> None:
        """
        Sets the state of a key.

        Parameters
        ----------
        key: `KeyLike`
            The key to set the state of.
        state: `StateLike`
            The state to set.
        """

        self._states[Key.convert(key)] = State.convert(state)

    def is_state(self, key: KeyLike, state: StateLike, /) -> bool:
        """
        Checks if a key is in a certain state.
        State can be State.none to check if the key is not being interacted with at all.\n
        Equivalent to `self.get_state(key) == state`.

        Parameters
        ----------
        key: `KeyLike`
            The key to check.
        state: `StateLike`
            The state to check for.

        Returns
        -------
        `bool`
            Whether the key is in the specified state.
        """

        return self.get_state(key) == State.convert(state)

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

    def is_active(self, keybinding: Keybinding, /) -> bool:
        """
        Checks if a keybinding is active.

        Parameters
        ----------
        keybinding: `Keybinding`
            The keybinding to check.

        Returns
        -------
        `bool`
            Whether the keybinding is active.
        """

        return all(self.is_state(key, state) for key, state in keybinding)

    def is_inactive(self, keybinding: Keybinding, /) -> bool:
        """
        Checks if a keybinding is inactive.

        Parameters
        ----------
        keybinding: `Keybinding`
            The keybinding to check.

        Returns
        -------
        `bool`
            Whether the keybinding is inactive.
        """

        return not self.is_active(keybinding)

    def any(self, state: StateLike = State.none, /) -> bool:
        """
        Checks if any key is in a certain state.

        Parameters
        ----------
        state: `StateLike`
            The state to check for.
            If no state is specified, checks if any key is being interacted with at all, i.e. in any state except `State.none`.

        Returns
        -------
        `bool`
            Whether any key is in the specified state.
        """

        state = State.convert(state)

        return any(
            self.get_state(key) == state
            if state != State.none
            else self.get_state(key) != State.none
            for key in self._states
        )

    def add_keybinding(
        self, keybinding: Keybinding | tuple[KeyLike, Callable[[], None]], /
    ) -> None:
        """
        Adds a keybinding to the keyboard.

        Parameters
        ----------
        keybinding: `Keybinding`
            The keybinding to add.
        """

        self._keybindings.append(
            keybinding
            if isinstance(keybinding, Keybinding)
            else Keybinding.make(keybinding[0], action=keybinding[1])
        )

    def add_keybindings(
        self, keybindings: list[Keybinding] | dict[KeyLike, Callable[[], None]]
    ) -> None:
        """
        Adds a list of keybindings, or serves as a helper method for adding many simple, key to action, modifier-less keybindings.

        Parameters
        ----------
        keybindings: `list[Keybinding] | dict[KeyLike, Callable[[], None]]`
            The list of keybindings to add or a `KeyLike` to action mapping for the keybindings to be created.
        """

        if isinstance(keybindings, list):
            for keybinding in keybindings:
                self.add_keybinding(keybinding)
            return

        for key, action in keybindings.items():
            self.add_keybinding(Keybinding.make(key, action=action))

    def remove_keybinding(self, keybinding: Keybinding, /) -> None:
        """
        Removes a keybinding from the keyboard.

        Parameters
        ----------
        keybinding: `Keybinding`
            The keybinding to remove.

        Raises
        ------
        `ValueError`
            If the keybinding is not found.
        """

        self._keybindings.remove(keybinding)

    def get_axis(
        self, neg: KeyLike, pos: KeyLike, /, *, state: StateLike = State.pressed
    ) -> float:
        """
        Gets the axis value of a key.

        Parameters
        ----------
        neg: `KeyLike`
            The key to check for negative values.
        pos: `KeyLike`
            The key to check for positive values.
        state: `StateLike`
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

        state = State.convert(state)

        assert state != State.none

        return int(self.is_state(pos, state)) - int(self.is_state(neg, state))

    def get_movement_2d(
        self,
        horizontal_axis: tuple[KeyLike, KeyLike],
        vertical_axis: tuple[KeyLike, KeyLike],
        /,
        *,
        state: StateLike = State.pressed,
        normalize: bool = True,
    ) -> Vector2:
        """
        Two axis to use for movement.

        Example
        -------
        ```python
        app.keyboard.get_movement_2d(("a", "d"), ("w", "s"))  # wasd
        ```

        Parameters
        ----------
        vertical_axis: `tuple[KeyLike, KeyLike]`
            The keys to check for vertical movement.
        horizontal_axis: `tuple[KeyLike, KeyLike]`
            The keys to check for horizontal movement.
        state: `StateLike`
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
            self.get_axis(*horizontal_axis, state=state),
            self.get_axis(*vertical_axis, state=state),
        )

        return movement.normalize() if normalize else movement

    def get_movement_3d(
        self,
        horizontal_axis: tuple[KeyLike, KeyLike],
        vertical_axis: tuple[KeyLike, KeyLike],
        forward_axis: tuple[KeyLike, KeyLike],
        /,
        *,
        state: StateLike = State.pressed,
        order: Literal["XYZ", "XZY"] = "XYZ",
        normalize: bool = True,
    ) -> Vector3:
        """
        Three axis to use for movement.\n
        Ordering defaults to "XYZ" (horizontal, vertical, forward) but can be changed to "XZY" (horizontal, forward, vertical).

        Parameters
        ----------
        vertical_axis: `tuple[KeyLike, KeyLike]`
            The keys to check for vertical movement.
        horizontal_axis: `tuple[KeyLike, KeyLike]`
            The keys to check for horizontal movement.
        forward_axis: `tuple[KeyLike, KeyLike]`
            The keys to check for forward movement.
        state: `StateLike`
            The state to check for. Cannot be `State.none`. Defaults to `State.pressed`.
        order: `Literal["XYZ", "XZY"]`
            The order of the axes. Defaults to "XYZ".
        normalize: `bool`
            Whether to normalize the movement to the range [0, 1]. Defaults to `True`.

        Returns
        -------
        `Vector3`
            The movement of the keys.

        Raises
        ------
        `AssertionError`
            If `state` is `State.none`.
        """
        movement = Vector3(
            self.get_axis(*horizontal_axis, state=state),
            self.get_axis(*vertical_axis, state=state),
            self.get_axis(*forward_axis, state=state),
        )

        if order == "XZY":
            movement = Vector3(movement.xzy)  # pygame.math.Vector3 -> sky.Vector3

        return movement.normalize() if normalize else movement
