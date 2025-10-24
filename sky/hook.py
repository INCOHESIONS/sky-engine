from __future__ import annotations

import functools
from bisect import insort
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Literal, Self, get_type_hints

from .types import Coroutine
from .utils import first

if TYPE_CHECKING:
    from sky import App

__all__ = ["Hook"]


class Hook[TCallback: Callable[..., Any] = Callable[[], None]]:
    """
    A `Hook` that can be listened to.

    ## Usage
    ```python
    from sky import Hook

    on_something = Hook()

    on_something += lambda: print("something happened")

    # [...] once something happens:
    on_something.notify()  # notifies all callbacks
    ```

    They can also be used as decorators:
    ```python
    from sky import App

    app = App()


    @app.setup
    def setup() -> None:
        print("setup")


    app.mainloop()
    ```

    They can also be used as decorators in coroutines:
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

    They can also be added with priorities:
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

    They can also be cancelled: if a callback returns a truthy value, and `cancellable` is set to `True`, execution of all following callbacks is stopped.
    ```python
    from typing import Callable

    from sky import Hook

    on_something = Hook[Callable[[], bool]](cancellable=True)


    @on_something
    def callback1() -> bool:
        print("callback1")
        return True


    @on_something
    def callback2() -> bool:
        print("this will not execute")
        return False


    on_something.notify()
    ```

    They can also be set to only be able to be called once:
    ```python
    from sky import Hook

    on_something = Hook(once=True)


    @on_something
    def some_callback() -> None: ...


    on_something.notify()
    on_something.notify()  # raises RuntimeError. you can check if it's already been called at least once with the `on_something.called` property
    ```
    """

    app: ClassVar[App]

    def __init__(
        self,
        callbacks: list[TCallback] | None = None,
        /,
        *,
        cancellable: bool = False,
        once: bool = False,
    ) -> None:
        self._callbacks: list[tuple[TCallback, int]] = [(c, 0) for c in callbacks or []]
        self._cancellable = cancellable
        self._once = once
        self._called = False

    def __iter__(self) -> Iterator[TCallback]:
        return iter(c for c, _ in self._callbacks)

    def __call__[C: Callable[[], Coroutine]](
        self, callback: TCallback | C, /
    ) -> TCallback | C:
        if get_type_hints(callback).get("return", None) is Coroutine:

            def __add(*args: Any, **kwargs: Any) -> None:  # pyright: ignore[reportUnusedParameter]
                self.app.executor.start_coroutine(callback)

            self.add_callback(__add)  # pyright: ignore[reportArgumentType]
        else:
            self.add_callback(callback)  # pyright: ignore[reportArgumentType]

        return callback

    def __imatmul__(self, callback_with_priority: tuple[TCallback, int], /) -> Self:
        self.add_callback(callback_with_priority[0], priority=callback_with_priority[1])
        return self

    def __iadd__(self, callback: TCallback, /) -> Self:
        self.add_callback(callback)
        return self

    def __isub__(self, callback: TCallback, /) -> Self:
        self.remove_callback(callback)
        return self

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

    def add_callback(
        self, callback: TCallback, /, *, priority: Literal["min", "max"] | int = 0
    ) -> None:
        """
        Adds a callback to the list of callbacks.

        Parameters
        ----------
        callback: `TCallback`
            The callback to add.
        priority: `Literal["min", "max"] | int`
            The priority of the callback.\n
            If set to `"min"`, the callback will be added with a priority of the current lowest priority callback minus 1. If this is the first callback being added, it will have a priority of `-100`.\n
            If set to `"max"`, the callback will be added with a priority of the current highest priority callback plus 1. If this is the first callback being added, it will have a priority of `100`.\n
            If set to an `int`, the callback will simply be added with that priority.
        """

        if isinstance(priority, str):
            if priority == "min":
                priority = min((p for _, p in self._callbacks), default=-99) - 1
            elif priority == "max":
                priority = max((p for _, p in self._callbacks), default=99) + 1

        insort(self._callbacks, (callback, priority), key=lambda x: -x[1])

    def remove_callback(self, callback: TCallback, /) -> None:
        """
        Removes a callback to the list of callbacks.

        Parameters
        ----------
        callback: `TCallback`
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

    def notify(self, /, *args: Any, **kwargs: Any) -> None:
        """
        Notifies all callbacks.

        Raises
        ------
        `RuntimeError`
            If the `Hook` was set to `once` and was already called.
        """

        if self._once and self._called:
            raise RuntimeError("Hook with `once` set to `True` was already called.")

        for callback in self:
            if callback(*args, **kwargs) and self._cancellable:
                break

        if self._once:
            self.clear()

        self._called = True

    invoke = notify  # alias

    def equals(
        self, *args: Any
    ) -> Callable[[Callable[[], None]], Callable[[TCallback], None]]:
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
        *args : `Any`
            The arguments to check against.

        Returns
        -------
        `Callable[[Callable[[], None]], Callable[[TCallback], None]]`
            The decorated function.
        """

        def decorator(func: Callable[[], None]) -> Callable[[TCallback], None]:
            nonlocal self

            @functools.wraps(func)
            def wrapper(*args2: TCallback) -> None:
                if args == args2:
                    func()

            # there's no way to cast `wrapper` to `T` here, and since python doesn't support extracting
            # the type of the arguments of a callable in some crazy typescript-like way, we have to do this
            self += wrapper  # pyright: ignore[reportUnknownVariableType, reportOperatorIssue]

            return wrapper

        return decorator
