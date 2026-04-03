from inspect import isgeneratorfunction
from typing import Callable, Self, final, override

from ..core import Service
from ..types import Coroutine
from ..utils import attempt_empty_call
from ..yieldable import WaitForFrames, WaitUntil, Yieldable


@final
class Executor(Service):
    """Handles `Coroutine`s."""

    def __init__(self) -> None:
        self._coroutines: dict[Coroutine, Yieldable] = {}

    def __iadd__(self, coroutine: Callable[[], Coroutine] | Coroutine, /) -> Self:
        self.start_coroutine(coroutine)
        return self

    def __isub__(self, coroutine: Coroutine, /) -> Self:
        self.stop_coroutine(coroutine)
        return self

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

        if not self.app.is_running:

            def __coro() -> Coroutine:
                yield WaitUntil(lambda: self.app.is_running)
                yield from coroutine

            self._step_coroutine(coro := __coro())
            return coro

        self._step_coroutine(coroutine)

        return coroutine

    schedule = start_coroutine  # alias

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

    unschedule = stop_coroutine  # alias

    def stop_all_coroutines(self) -> None:
        """Stops all currently running `Coroutine`s."""

        self._coroutines.clear()

    unschedule_all = stop_all_coroutines  # alias

    @override
    def update(self) -> None:
        for coroutine, yieldable in list(self._coroutines.items()):
            if yieldable.is_ready():
                self._step_coroutine(coroutine)

    def loop(
        self,
        func: Callable[[], None] | Callable[[], Coroutine],
        /,
        *,
        period: Callable[[], Yieldable],
        delay: Callable[[], Yieldable] | None = None,
    ) -> None:
        def __coro() -> Coroutine:
            if delay:
                yield delay()

            while self.app.is_running:
                if isgeneratorfunction(func):
                    yield from func()
                else:
                    func()

                yield period()

        self.start_coroutine(__coro)

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
            return None

        if isinstance(value, type):
            return attempt_empty_call(
                value,
                err=f"Yieldable {value.__name__} cannot be instanced without arguments!",
            )

        return value or WaitForFrames()
