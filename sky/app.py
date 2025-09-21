from inspect import signature
from typing import Self

import pygame

from sky.listenable import Listenable

from .components import Chrono, Events, Executor, Keyboard, Mouse, Windowing
from .core import Component, Yieldable, singleton
from .spec import AppSpec
from .utils import first, get_by_attrs

__all__ = ["App"]


@singleton
class App:
    """
    The singleton `App` class.\n
    Pre-execution configuration is defined with `AppSpec`, such as the main window's title and size.

    Components:
        - `Events` (handles pygame events)
        - `Keyboard` (handles keyboard input)
        - `Mouse` (handles mouse input)
        - `Windowing` (handles windowing)
        - `Chrono` (handles time)
        - `Executor` (handles coroutines)

    User-defined components can be added by subclassing `Component` and using the `add_component` method (can be used as a class decorator).

    Listenables:
        - `setup` (executed after components are started up, and before the first frame)
        - `teardown` (executed before components are stopped, and after the last frame)
        - `pre_update` (executed before components are updated)
        - `post_update` (executed after components are updated)
    """

    def __init__(self, /, *, spec: AppSpec = AppSpec()) -> None:
        pygame.init()

        Listenable.app = self
        Yieldable.app = self
        Component.app = self

        self.spec = spec
        """The app's specification, i.e., pre-execution configuration."""

        self.setup = Listenable()
        """Executes after components are started up, and before the first frame."""

        self.teardown = Listenable()
        """Executes before components are stopped, and after the last frame."""

        self.pre_update = Listenable()
        """Executes before components are updated."""

        self.post_update = Listenable()
        """Executes after components are updated."""

        self.events = Events()
        """Handles pygame events."""

        self.keyboard = Keyboard()
        """Handles keyboard input."""

        self.mouse = Mouse()
        """Handles mouse input."""

        self.windowing = Windowing()
        """Handles windowing."""

        self.chrono = Chrono()
        """Handles time."""

        self.executor = Executor()
        """Handles coroutines."""

        self._components: list[Component] = [
            self.events,
            self.keyboard,
            self.mouse,
            self.windowing,
            self.chrono,
            self.executor,
        ]  # do not change ordering

        for component in self._components:
            component._internal = True  # type: ignore

        self.is_running = True

    def mainloop(self) -> None:
        """
        The app's main loop.

        Order of execution:
            Pre-loop:
                1. Component.start
                2. App.setup
            During loop:
                1. App.pre_update
                2. Component.update
                3. App.post_update
            Post-loop:
                1. App.teardown
                2. Component.stop

        App.teardown is called before Component.stop since dependencies on it might need information that components have.
        """

        for component in self._components:
            component.start()

        self.setup.notify()

        self.is_running = True

        while not self._should_quit():
            self.events._events = pygame.event.get()  # type: ignore

            self.pre_update.notify()

            for component in self._components:
                component.update()

            self.post_update.notify()

        self.teardown.notify()

        for component in self._components:
            component.stop()

        self.is_running = False

        pygame.quit()

    run = mainloop

    def add_component(self, component: type[Component] | Component, /) -> Self:
        """
        Adds a component to the app. Can be used as a class decorator.
        If a type is passed, it will be immediately initialized with no arguments as long as its constructor takes no arguments, otherwise an error will be raised.

        Parameters
        ----------
        component: `type[Component] | Component`
            The component, or its type, to add. Will be instanced immediately if a type is passed.

        Returns
        -------
        Self
            The app, for chaining.

        Raises
        ------
        `ValueError`
            If a type is passed that has a constructor that takes arguments.
        """

        if callable(component) and len(signature(component).parameters) > 0:
            raise ValueError(
                f"Component types must have constructors that take no arguments to be passed in directly to `add_component` (problematic type: {component.__name__})."
            )

        self._components.append(component() if callable(component) else component)
        return self

    def remove_component(self, component: type[Component] | Component, /) -> None:
        """
        Removes a component from the app.

        Parameters
        ----------
        component: `type[Component] | Component`
            The component, or its type, to remove. Will try and find a component of matching type if a type is passed. That type will not be instanced.\n
            If the component is an internal component (such as `Events` or `Windowing`), an error will be raised.

        Raises
        ------
        `ValueError`
            If the component is an internal component or if the component was not found.
        """

        if isinstance(component, type):
            component = self.get_component(component)  # type: ignore

        if getattr(component, "_internal", False):
            raise ValueError("Cannot remove internal component")

        self._components.remove(component)  # type: ignore

    def get_component[T: Component](self, component: type[T] | str, /) -> T | None:
        """
        Gets a component from the app.

        Parameters
        ----------
        component: `type[Component] | str`
            The component's type's name, or the type itself.

        Returns
        -------
        `Component | None`
            The component, if found.
        """

        return (
            first(components)
            if (components := self.get_components(component)) is not None
            else None
        )

    def get_components[T: Component](
        self, component: type[T] | str, /
    ) -> list[T] | None:
        return list(
            filter(lambda c: c.__class__.__name__ == component, self._components)  # type: ignore
            if isinstance(component, str)
            else filter(lambda c: isinstance(c, component), self._components)  # type: ignore
        )

    def quit(self) -> None:
        """Closes the app in the next frame."""

        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _should_quit(self) -> bool:
        return get_by_attrs(self.events, type=pygame.QUIT) is not None
