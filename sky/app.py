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
    """The singleton app class."""

    def __init__(self, /, *, spec: AppSpec = AppSpec()) -> None:
        pygame.init()

        Listenable.app = self
        Yieldable.app = self
        Component.app = self

        self.spec = spec

        self.setup = Listenable()
        self.teardown = Listenable()

        self.pre_update = Listenable()
        self.post_update = Listenable()

        self.events = Events()
        self.keyboard = Keyboard()
        self.mouse = Mouse()
        self.windowing = Windowing()
        self.chrono = Chrono()
        self.executor = Executor()

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

        self._is_running = True

    @property
    def is_running(self) -> bool:
        """Whether the app is running."""

        return self._is_running

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

        self._is_running = True

        while not self._should_quit():
            self.events._events = pygame.event.get()  # type: ignore

            self.pre_update.notify()

            for component in self._components:
                component.update()

            self.post_update.notify()

        self.teardown.notify()

        for component in self._components:
            component.stop()

        self._is_running = False

        pygame.quit()

    run = mainloop

    def add_component(self, component: type[Component] | Component, /) -> Self:
        """
        Adds a component to the app. Can be used as a class decorator.

        Parameters
        ----------
        component: type[Component] | Component
            The component, or its type, to add. Will be instanced immediately if a type is passed.

        Returns
        -------
        Self
            The app, for chaining.
        """

        self._components.append(
            component() if isinstance(component, type) else component
        )
        return self

    def remove_component(self, component: type[Component] | Component, /) -> None:
        """
        Removes a component from the app.

        Parameters
        ----------
        component: type[Component] | Component
            The component, or its type, to remove. Will try and find a component of matching type if a type is passed. That type will not be instanced.
            If the component is an internal component (such as `Events` or `Windowing`), an error will be raised.
        """

        if getattr(component, "_internal", False):
            raise ValueError("Cannot remove internal component")

        if isinstance(component, type):
            self._components.remove(
                first(filter(lambda c: isinstance(c, component), self._components))  # type: ignore
            )
            return

        self._components.remove(component)

    def get_component[T: Component](self, component: type[T] | str, /) -> T | None:
        """
        Gets a component from the app.

        Parameters
        ----------
        component: type[Component] | str
            The component's type's name, or the type itself.

        Returns
        -------
        Component | None
            The component, if found.
        """

        if isinstance(component, str):
            return first(
                filter(lambda c: c.__class__.__name__ == component, self._components)  # type: ignore
            )

        return first(filter(lambda c: isinstance(c, component), self._components))  # type: ignore

    def quit(self) -> None:
        """Closes the app in the next frame."""

        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _should_quit(self) -> bool:
        return get_by_attrs(self.events, type=pygame.QUIT) is not None
