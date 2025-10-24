from typing import Callable, final, override

from sky.utils import callable_with_no_arguments

from ..core import Component
from ..types import Coroutine
from ..yieldable import WaitForFrames, Yieldable


@final
class Executor(Component):
    """Handles coroutines."""

    def __init__(self) -> None:
        self._coroutines: dict[Coroutine, Yieldable] = {}

    def start_coroutine(
        self, coroutine: Callable[[], Coroutine] | Coroutine, /
    ) -> None:
        """
        Starts a Coroutine.

        Parameters
        ----------
        coroutine : `Callable[[], Coroutine] | Coroutine`
            A `Coroutine` or a `Callable` that returns a `Coroutine`.

        Raises
        ------
        `RuntimeError`
            If the coroutine is already running.
        """

        if callable(coroutine):
            coroutine = coroutine()

        if coroutine in self._coroutines:
            raise RuntimeError("The same exact coroutine cannot be added twice.")

        self._step_coroutine(coroutine)

    def stop_coroutine(self, coroutine: Coroutine, /) -> None:
        """
        Stops the given `Coroutine`.

        Parameters
        ----------
        coroutine : `Coroutine`
            The `Coroutine` to be stopped.

        Raises
        ------
        `KeyError`
            If the `Coroutine` is not found.
        """

        self._coroutines.pop(coroutine)

    def stop_all_coroutines(self) -> None:
        """Stops all `Coroutine`s."""

        self._coroutines.clear()

    @override
    def update(self) -> None:
        for coroutine, yieldable in list(self._coroutines.items()):
            if yieldable.is_ready():
                self._step_coroutine(coroutine)

    def _step_coroutine(self, coroutine: Coroutine, /) -> None:
        next = self._get_next(coroutine)

        if next is not None:
            self._coroutines[coroutine] = next
        else:
            self.stop_coroutine(coroutine)

    def _get_next(self, coroutine: Coroutine, /) -> Yieldable | None:
        try:
            value = next(coroutine)
        except StopIteration:
            return None

        if isinstance(value, type):
            if callable_with_no_arguments(value):
                return value()

            raise RuntimeError(
                f"The type ({value.__name__}) cannot be instanced without arguments!"
            )

        return value or WaitForFrames()
