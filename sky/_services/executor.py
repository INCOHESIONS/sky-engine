from typing import Callable, final, override

from ..core import Service
from ..types import Coroutine
from ..utils import attempt_empty_call
from ..yieldable import WaitForFrames, Yieldable


@final
class Executor(Service):
    """Handles `Coroutine`s."""

    def __init__(self) -> None:
        self._coroutines: dict[Coroutine, Yieldable] = {}

    def __contains__(self, coroutine: Coroutine, /) -> bool:
        return self.is_active(coroutine)

    @override
    def stop(self) -> None:
        self.stop_all_coroutines()

    def start_coroutine(
        self, coroutine: Callable[[], Coroutine] | Coroutine, /
    ) -> Coroutine:
        """
        Starts a `Coroutine`.

        Parameters
        ----------
        coroutine: `Callable[[], Coroutine] | Coroutine`
            A `Coroutine` or a `Callable` that returns a `Coroutine`.

        Returns
        -------
        `Coroutine`
            The added `Coroutine`.

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

        return coroutine

    def stop_coroutine(self, coroutine: Coroutine, /) -> None:
        """
        Stops the given `Coroutine`.

        Parameters
        ----------
        coroutine: `Coroutine`
            The `Coroutine` to be stopped.

        Raises
        ------
        `KeyError`
            If the `Coroutine` is not found.
        """

        self._coroutines.pop(coroutine)

    def stop_all_coroutines(self) -> None:
        """Stops all currently running `Coroutine`s."""

        self._coroutines.clear()

    @override
    def update(self) -> None:
        for coroutine, yieldable in list(self._coroutines.items()):
            if yieldable.is_ready():
                self._step_coroutine(coroutine)

    def is_active(self, coroutine: Coroutine, /) -> bool:
        """
        Checks if a `Coroutine` is currently being executed.

        Parameters
        ----------
        coroutine: `Coroutine`
            The `Coroutine` to check.

        Returns
        -------
        `bool`
            If the `Coroutine` is currently being executed.
        """

        return coroutine in self._coroutines

    def _step_coroutine(self, coroutine: Coroutine, /) -> None:
        if n := self._get_next(coroutine):
            self._coroutines[coroutine] = n
        else:
            self.stop_coroutine(coroutine)

    def _get_next(self, coroutine: Coroutine, /) -> Yieldable | None:
        try:
            value = next(coroutine)
        except StopIteration:
            return (
                then
                if (then := getattr(self._coroutines[coroutine], "_then", None))
                else None
            )

        if isinstance(value, type):
            return attempt_empty_call(
                value,
                message=f"The type ({value.__name__}) cannot be instanced without arguments!",
            )

        return value or WaitForFrames()
