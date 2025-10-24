"""Core engine functionality."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import KW_ONLY, dataclass, field
from typing import TYPE_CHECKING, Callable, ClassVar, Self, final

from singleton_decorator import (  # pyright: ignore[reportMissingTypeStubs]
    singleton as untyped_singleton,  # pyright: ignore[reportUnknownVariableType]
)

from .enums import Key, Modifier, State
from .hook import Hook
from .types import Coroutine

if TYPE_CHECKING:
    from .app import App

__all__ = [
    "Component",
    "Keybinding",
    "singleton",
]


@final
@dataclass(slots=True)
class Keybinding:
    """Defines a keybinding."""

    _: KW_ONLY

    keymap: dict[Key, State]

    on_activation: Hook = field(default_factory=Hook)
    on_deactivation: Hook = field(default_factory=Hook)

    def __post_init__(self):
        if not self.keymap:
            raise ValueError("Keybinding must have at least one key")

    def __iter__(self) -> Iterator[tuple[Key, State]]:
        return iter(self.keymap.items())

    @classmethod
    def make(
        cls,
        key: Key,
        /,
        *,
        action: Callable[[], None],
        modifier: Modifier | None = None,
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

        if modifier is not None:
            return cls(
                keymap={modifier.value: State.pressed, key: state},
                on_activation=Hook([action]),
            )

        return cls(keymap={key: state}, on_activation=Hook([action]))


class Component:
    """Base class for components."""

    app: ClassVar[App]

    def start(self) -> Coroutine | None:
        """Runs before the first frame, after `entrypoint` and before `setup`. Can be a Coroutine."""

    def stop(self) -> Coroutine | None:
        """Runs after the last frame, after `teardown` and before `cleanup`. Can be a Coroutine."""

    def update(self) -> None:
        """Runs every frame, after `pre_update` and before `post_update`."""


def singleton[T: type](cls: T) -> T:
    """Makes the decorated class a singleton while properly keeping its type."""

    return untyped_singleton(cls)  # pyright: ignore[reportReturnType]
