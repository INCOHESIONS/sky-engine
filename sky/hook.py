from __future__ import annotations

import functools
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Self, get_type_hints

from .types import Coroutine

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
    from sky import App, WaitForSeconds
    from sky.colors import BLUE, RED
    from sky.types import Coroutine

    app = App()


    @app.setup
    def change_bg_color() -> Coroutine:
        app.window.surface.fill(RED)
        yield WaitForSeconds(3)
        app.window.surface.fill(BLUE)


    app.mainloop()
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

    def __init__(self, cancellable: bool = False, once: bool = False) -> None:
        self._callbacks: list[TCallback] = []
        self._cancellable = cancellable
        self._once = once
        self._called = False

    def __iter__(self) -> Iterator[TCallback]:
        return iter(self._callbacks)

    def __call__[V: Callable[[], Coroutine]](
        self, callback: TCallback | V
    ) -> TCallback | V:
        """Allows Hooks to be used as decorators."""

        if get_type_hints(callback).get("return", None) is Coroutine:

            def __add(*args: Any, **kwargs: Any) -> None:  # pyright: ignore[reportUnusedParameter]
                self.app.executor.start_coroutine(callback)

            self.add_callback(__add)  # pyright: ignore[reportArgumentType]
        else:
            self.add_callback(callback)  # pyright: ignore[reportArgumentType]

        return callback

    def __iadd__(self, callback: TCallback) -> Self:
        self.add_callback(callback)
        return self

    def __isub__(self, callback: TCallback) -> Self:
        self.remove_callback(callback)
        return self

    @property
    def called(self) -> bool:
        """Whether or not this Hook has already notified its callbacks at least once."""

        return self._called

    def add_callback(self, callback: TCallback, /) -> None:
        """
        Adds a callback to the list of callbacks.

        Parameters
        ----------
        callback: `TCallback`
            The callback to add.
        """

        self._callbacks.append(callback)

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

        self._callbacks.remove(callback)

    def clear(self) -> None:
        """Clears the list of callbacks."""

        self._callbacks.clear()

    def notify(self, /, *args: Any, **kwargs: Any) -> None:
        """
        Notifies all callbacks

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
