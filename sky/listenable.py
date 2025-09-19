from __future__ import annotations

from typing import Any, Callable, Iterator, Self

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
    """

    def __init__(self, cancellable: bool = False, once: bool = False) -> None:
        self._listeners: list[TListener] = []
        self._cancellable = cancellable
        self._once = once
        self._called = False

    def __iter__(self) -> Iterator[TListener]:
        return iter(self._listeners)

    def __call__(self, listener: TListener) -> Self:
        """Allows listenables to be used as decorators."""
        self.add_listener(listener)
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
