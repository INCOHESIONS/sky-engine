"""Contains the `Hook` class."""

from __future__ import annotations

import functools
from bisect import insort
from collections.abc import Iterator, Sequence
from operator import itemgetter
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Literal,
    Self,
    get_type_hints,
    overload,
)

from .sentinel import Sentinel
from .types import Coroutine
from .utils import first, mapl

if TYPE_CHECKING:
    from .app import App

__all__ = ["Hook"]

_NOT_EXECUTED = Sentinel("NOT_EXECUTED")


class Hook[**TParams = [], TReturn: Any = None]:
    """
    A `Hook` that can have callbacks registered to it.

    ## Examples
    ### Simple usage:
    ```python
    from sky import Hook

    on_something = Hook()

    on_something += lambda: print("something happened")

    # [...] once something happens:
    on_something.notify()  # notifies all callbacks
    ```

    ### Decorator:
    ```python
    from sky import App

    app = App()


    @app.setup
    def setup() -> None:
        print("setup")


    app.mainloop()
    ```

    ### Decorator in a `Coroutine`:
    ```python
    from sky import App, WaitForSeconds, Coroutine
    from sky.colors import BLUE, RED

    app = App()


    @app.setup
    def change_bg_color() -> Coroutine:
        app.window.surface.fill(RED)
        yield WaitForSeconds(3)
        app.window.surface.fill(BLUE)


    app.mainloop()
    ```

    ### Callback registration with priority:
    ```python
    from sky import Hook

    on_something = Hook()


    def callback1() -> None:
        print("This will execute second")


    def callback2() -> None:
        print("This will execute first")


    on_something.add_callback(callback1, priority=0)
    on_something.add_callback(callback2, priority=100)


    on_something.notify()
    ```

    ### Gathering results from callbacks:
    ```python
    from sky import Hook

    on_something = Hook[[float], float]()


    @on_something
    def square(v: float) -> float:
        return v**2


    @on_something
    def cube(v: float) -> float:
        return v**3


    print(on_something.notify(3))
    ```

    ### Callback cancellation:
    ```python
    from sky import Hook

    on_something = Hook(cancellable=True)


    @on_something
    def will_exec() -> None:
        print("This will execute")
        on_something.cancel()


    @on_something
    def wont_exec() -> None:
        print("This won't")


    on_something.notify()
    ```

    ### Preventing recalling with `once`:
    ```python
    from sky import Hook

    on_something = Hook(once=True)


    @on_something
    def callback() -> None: ...


    on_something.notify()
    on_something.notify()  # raises `RuntimeError`. you can check if it's already been called at least once with the `on_something.called` property.
    ```
    """

    app: ClassVar[App]

    def __init__(
        self,
        callbacks: list[Callable[TParams, TReturn]] | None = None,
        /,
        *,
        cancellable: bool = False,
        once: bool = False,
    ) -> None:
        self._callbacks: list[tuple[Callable[TParams, TReturn], int]] = [
            (c, 0) for c in callbacks or []
        ]

        self._cancellable = cancellable
        self._cancelled = False

        self._once = once
        self._called = False

    def __iter__(self) -> Iterator[Callable[TParams, TReturn]]:
        return iter(c for c, _ in self._callbacks)

    @overload
    def __call__(
        self, callback: Callable[TParams, Coroutine], /
    ) -> Callable[TParams, Coroutine]: ...

    @overload
    def __call__(
        self, callback: Callable[TParams, TReturn], /
    ) -> Callable[TParams, TReturn]: ...

    def __call__[TCallable: Callable[..., Any]](
        self, callback: TCallable, /
    ) -> TCallable:
        if get_type_hints(callback).get("return", None) is Coroutine:

            def __add(*args: TParams.args, **kwargs: TParams.kwargs) -> TReturn:
                self.app.executor.start_coroutine(callback(*args, **kwargs))
                return None  # pyright: ignore[reportReturnType]

            self.add_callback(__add)
        else:
            self.add_callback(callback)

        return callback

    def __imatmul__(
        self, callback_with_priority: tuple[Callable[TParams, TReturn], int], /
    ) -> Self:
        self.add_callback(callback_with_priority)
        return self

    def __iadd__(self, callback: Callable[TParams, TReturn], /) -> Self:
        self.add_callback(callback)
        return self

    def __isub__(self, callback: Callable[TParams, TReturn], /) -> Self:
        self.remove_callback(callback)
        return self

    def __contains__(self, callback: Callable[TParams, TReturn], /) -> bool:
        return callback in self.callbacks

    @property
    def callbacks(self) -> Sequence[Callable[TParams, TReturn]]:
        return mapl(itemgetter(0), self._callbacks)

    @property
    def cancellable(self) -> bool:
        """Whether or not this `Hook` can be cancelled."""

        return self._cancellable

    @property
    def once(self) -> bool:
        """Whether or not this `Hook` can only be called once."""

        return self._once

    @property
    def called(self) -> bool:
        """Whether or not this `Hook` has already notified its callbacks at least once."""

        return self._called

    @overload
    def add_callback(
        self,
        callback: tuple[Callable[TParams, TReturn], int],
        /,
    ) -> None: ...

    @overload
    def add_callback(
        self,
        callback: Callable[TParams, TReturn],
        /,
        *,
        priority: Literal["min", "max"] | int = 0,
    ) -> None: ...

    def add_callback(
        self,
        callback: tuple[Callable[TParams, TReturn], int] | Callable[TParams, TReturn],
        /,
        *,
        priority: Literal["min", "max"] | int = 0,
    ) -> None:
        """
        Adds a callback to the list of callbacks.

        Parameters
        ----------
        callback: `Callable[TParams, TReturn]`
            The callback to add.
        priority: `Literal["min", "max"] | int`
            The priority of the callback.\n
            If set to `"min"`, the callback will be added with a priority of the current lowest priority callback minus 1. If this is the first callback being added, it will have a priority of `-100`.\n
            If set to `"max"`, the callback will be added with a priority of the current highest priority callback plus 1. If this is the first callback being added, it will have a priority of `100`.\n
            If set to an `int`, the callback will simply be added with that priority.
        """

        if isinstance(callback, tuple):
            callback, priority = callback

        if isinstance(priority, str):
            if priority == "min":
                priority = min((p for _, p in self._callbacks), default=-99) - 1
            elif priority == "max":
                priority = max((p for _, p in self._callbacks), default=99) + 1

        insort(self._callbacks, (callback, priority), key=lambda x: -x[1])

    def remove_callback(self, callback: Callable[TParams, TReturn], /) -> None:
        """
        Removes a callback to the list of callbacks.

        Parameters
        ----------
        callback: `Callable[TParams, TReturn]`
            The callback to remove.

        Raises
        ------
        `ValueError`
            If the callback wasn't found.
        """

        if (
            remove := first(filter(lambda c: c[0] == callback, self._callbacks))
        ) is None:
            raise ValueError("Callback not found.")

        self._callbacks.remove(remove)

    def clear(self) -> None:
        """Clears the list of callbacks."""

        self._callbacks.clear()

    def notify(self, /, *args: TParams.args, **kwargs: TParams.kwargs) -> list[TReturn]:
        """
        Notifies all callbacks.

        Parameters
        ----------
        *args: TParams.args
            Positional arguments to pass to the callbacks.
        **kwargs: TParams.kwargs
            Keyword arguments to pass to the callbacks.

        Returns
        -------
        list[TReturn]
            A list of all the values returned by the callbacks.

        Raises
        ------
        `RuntimeError`
            If the `Hook` was set to `once` and was already called.
        """

        if self._once and self._called:
            raise RuntimeError("Hook with `once` set to `True` was already called.")

        if not self._callbacks:
            return []

        results: list[TReturn] = []

        if not self._cancelled:
            for callback in self:
                if (result := callback(*args, **kwargs)) is not _NOT_EXECUTED:
                    results.append(result)

                if self._cancelled:
                    break

        if self._once:
            self.clear()

        self._called = True
        self._cancelled = False

        return results

    invoke = notify  # alias
    trigger = notify  # alias
    emit = notify  # alias

    def cancel(self) -> None:
        """
        Cancels the `Hook` and prevents any further callbacks from being invoked.

        Raises
        ------
        `RuntimeError`
            If the `Hook` is not cancellable.
        """

        if not self.cancellable:
            raise RuntimeError("Hook is not cancellable.")

        self._cancelled = True

    def equals(
        self, *args: TParams.args, **kwargs: TParams.kwargs
    ) -> Callable[[Callable[[], TReturn]], Callable[TParams, TReturn]]:
        """
        Prevents a handler from being invoked if the arguments passed to `invoke` don't match the arguments passed as `args`.

        Examples
        --------
        ```python
        @app.mouse.on_button_downed
        def on_button_downed(button: MouseButton) -> None:
            if button == MouseButton.left:
                ...
        ```

        Can be rewritten as:

        ```python
        @app.mouse.on_button_downed.equals(MouseButton.left)
        def on_button_downed() -> None: ...
        ```

        Parameters
        ----------
        *args: `TParams.args`
            The arguments to check against.
        **kwargs: `TParams.kwargs`
            The keyword arguments to check against.

        Returns
        -------
        `Callable[[Callable[[], None]], Callable[TParams, TReturn]]`
            The decorated function.
        """

        def decorator(
            func: Callable[[], TReturn],
        ) -> Callable[TParams, TReturn]:
            nonlocal self

            @functools.wraps(func)
            def wrapper(*args2: TParams.args, **kwargs2: TParams.kwargs) -> TReturn:
                if args == args2 and kwargs == kwargs2:
                    return func()
                return _NOT_EXECUTED  # pyright: ignore[reportReturnType]

            self += wrapper

            return wrapper

        return decorator

    def execute_once(
        self, callback: Callable[TParams, TReturn], /
    ) -> Callable[TParams, TReturn]:
        def proxy(*args: TParams.args, **kwargs: TParams.kwargs) -> TReturn:
            nonlocal self
            results = callback(*args, **kwargs)
            self -= proxy
            return results

        self += proxy

        return callback
