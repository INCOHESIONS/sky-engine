from typing import Callable, override

from ..core import Component, WaitForFrames, Yieldable
from ..types import Coroutine


class Executor(Component):
    """Handles coroutines."""

    def __init__(self) -> None:
        self._coroutines: dict[Coroutine, Yieldable] = {}

    def start_coroutine(
        self,
        coroutine: Callable[[], Coroutine] | Coroutine,
    ) -> None:
        """
        Starts a Coroutine.

        Parameters
        ----------
        coroutine : `Callable[[], Coroutine] | Coroutine`
            A `Coroutine` or a `Callable` that returns a `Coroutine`.
        """

        if callable(coroutine):
            coroutine = coroutine()

        if coroutine in self._coroutines:
            return

        self._step_coroutine(coroutine)

    def stop_coroutine(self, coroutine: Coroutine) -> None:
        """
        Stops the given `Coroutine`.

        Parameters
        ----------
        coroutine : `Coroutine`
            The `Coroutine` to be stopped.
        """

        self._coroutines.pop(coroutine)

    @override
    def update(self) -> None:
        for coroutine, yieldable in list(self._coroutines.items()):
            if yieldable.ready():
                self._step_coroutine(coroutine)

    def _step_coroutine(self, coroutine: Coroutine) -> None:
        next = self._get_next(coroutine)

        if next is not None:
            self._coroutines[coroutine] = next
        else:
            self.stop_coroutine(coroutine)

    def _get_next(self, coroutine: Coroutine) -> Yieldable | None:
        try:
            n = next(coroutine)
        except StopIteration:
            return None
        return n() if isinstance(n, type) else n if n is not None else WaitForFrames(1)
