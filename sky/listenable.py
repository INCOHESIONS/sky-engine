from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Callable, Iterator, Self, get_type_hints

from .types import Coroutine

if TYPE_CHECKING:
    from sky import App

__all__ = ["Listenable"]


class Listenable[TListener: Callable[..., Any] = Callable[[], None]]:
    """
    A sort of event that can be listened to.
    Isn't named Event to differentiate it from pygame.event.Event.

    ## Usage
    ```python
    from sky import Listenable

    on_something = Listenable()

    on_something += lambda: print("something happened")

    # [...] once something happens:
    on_something.notify()  # notifies all listeners
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

    They can also be cancelled: if a listener returns a truthy value, execution of all following listeners is stopped. This is only the case if cancellable is set to True.
    ```python
    from typing import Callable

    from sky import Listenable

    on_something = Listenable[Callable[[], bool]](cancellable=True)


    @on_something
    def listener1() -> bool:
        print("listener1")
        return True


    @on_something
    def listener2() -> bool:
        print("this will not execute")
        return False


    on_something.notify()
    ```

    Can also be used as a decorator in a coroutine:
    ```python
    from sky import App, WaitForSeconds
    from sky.colors import BLUE, RED
    from sky.types import Coroutine

    app = App()


    @app.setup
    def change_bg_color() -> Coroutine:
        assert app.windowing.surface is not None
        app.windowing.surface.fill(RED)
        yield WaitForSeconds(3)
        app.windowing.surface.fill(BLUE)


    app.mainloop()
    ```
    """

    app: App

    def __init__(self, cancellable: bool = False, once: bool = False) -> None:
        self._listeners: list[TListener] = []
        self._cancellable = cancellable
        self._once = once
        self._called = False

    def __iter__(self) -> Iterator[TListener]:
        return iter(self._listeners)

    def __call__(self, listener: TListener | Callable[[], Coroutine]) -> Self:
        """Allows listenables to be used as decorators."""

        if get_type_hints(listener)["return"] is Coroutine:

            def __add(*args: Any, **kwargs: Any) -> None:
                self.app.executor.start_coroutine(listener)

            self.add_listener(__add)  # type: ignore
            return self

        self.add_listener(listener)  # type: ignore
        return self

    def __iadd__(self, listener: TListener) -> Self:
        self.add_listener(listener)
        return self

    def __isub__(self, listener: TListener) -> Self:
        self.remove_listener(listener)
        return self

    def add_listener(self, listener: TListener, /) -> None:
        """
        Adds a listener to the list of listeners.

        Parameters
        ----------
        listener: TListener
            The listener to add.
        """

        self._listeners.append(listener)

    def remove_listener(self, listener: TListener, /) -> None:
        """
        Removes a listener to the list of listeners.

        Parameters
        ----------
        listener: TListener
            The listener to remove.
        """

        self._listeners.remove(listener)

    def clear(self) -> None:
        """Clears the list of listeners."""

        self._listeners.clear()

    def notify(self, *args: Any, **kwargs: Any) -> None:
        """Notifies all listeners"""

        if self._once and self._called:
            return

        for listener in self:
            if listener(*args, **kwargs) and self._cancellable:
                break

        self._called = True

    def equals(
        self, *args: Any
    ) -> Callable[[Callable[[], None]], Callable[[TListener], None]]:
        """
        Prevents a handler from being invoked if the arguments passed to `invoke` don't match the arguments passed as `args`.

        Examples
        --------
        ```python
        @app.mouse.on_button_downed
        def on_button_downed(button: MouseButton) -> None:
            if button == MouseButton.left: ...
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
        `Callable[[Callable[[], None]], Callable[[TListener], None]]`
            Blah blah blah. It's a decorator with arguments. No one knows how to type these.
        """

        def decorator(func: Callable[[], None]) -> Callable[[TListener], None]:
            nonlocal self

            @functools.wraps(func)
            def wrapper(*args2: TListener) -> None:
                if args == args2:
                    func()

            # there's no way to cast `wrapper` to `T` here, and since python doesn't support extracting
            # the type of the arguments of a callable in some crazy typescript-like way, we have to do this
            self += wrapper  # type: ignore

            return wrapper

        return decorator
