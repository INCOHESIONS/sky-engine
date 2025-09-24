from inspect import isgeneratorfunction, signature
from types import ModuleType
from typing import Callable, Self

import pygame

from .components import Chrono, Events, Executor, Keyboard, Mouse, Windowing
from .core import AppSpec, Component, singleton
from .listenable import Listenable
from .types import Coroutine
from .utils import first
from .yieldable import Yieldable

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
        Pre-loop:
            1. `entrypoint` (executed before components are started up, just after `mainloop` is called)
            2. `setup` (executed after components are started up, and before the first frame)
        During loop:
            1. `pre_update` (executed before components are updated)
            2. `post_update` (executed after components are updated)
        Post-loop:
            1. `teardown` (executed before components are stopped, and after the last frame)
            2. `cleanup` (executed after components are stopped, and before the app is destroyed. Cleans up any registered modules)
    """

    def __init__(self, /, *, spec: AppSpec = AppSpec()) -> None:
        pygame.init()

        Listenable.app = self
        Yieldable.app = self
        Component.app = self

        self.spec = spec
        """The app's specification, i.e., pre-execution configuration."""

        self.entrypoint = Listenable()
        """Executes before components are started up, just after `mainloop` is called."""

        self.setup = Listenable()
        """Executes after components are started up, and before the first frame."""

        self.pre_update = Listenable()
        """Executes before components are updated."""

        self.post_update = Listenable()
        """Executes after components are updated."""

        self.teardown = Listenable()
        """Executes before components are stopped, and after the last frame."""

        self.cleanup = Listenable()
        """Executes after components are stopped, and before the app is destroyed. Cleans up any registered modules."""

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
            self.mouse,
            self.keyboard,
            self.windowing,
            self.chrono,
            self.executor,
        ]  # do not change ordering

        for component in self._components:
            component._internal = True  # type: ignore

        self.is_running = True

    @property
    def window(self):
        """
        Short for `app.windowing.main_window`.

        Returns
        -------
        `_WindowWrapper`
            The main window.

        Raises
        ------
        `AssertionError`
            If the main window is not set (app is in headless mode).
        """

        assert self.windowing.main_window is not None
        return self.windowing.main_window

    def mainloop(self) -> None:
        """
        The app's main loop.

        Order of execution:
            Pre-loop:
                1. `App.entrypoint`
                2. `Component.start`
                3. `App.setup`
            During loop:
                1. `App.pre_update`
                2. `Component.update`
                3. `App.post_update`
            Post-loop:
                1. `App.teardown`
                2. `Component.stop`
                3. `App.cleanup`
        """

        self.entrypoint.notify()

        for component in self._components:
            self._handle_possible_coroutine(component.start)

        self.setup.notify()

        self.is_running = True

        while not self.events.has(pygame.QUIT):
            self.events.handle_events()

            self.pre_update.notify()

            for component in self._components:
                component.update()

            self.post_update.notify()

        self.is_running = False

        self.teardown.notify()

        for component in self._components:
            self._handle_possible_coroutine(component.stop)

        self.cleanup.notify()

        pygame.quit()

    run = mainloop  # alias

    def add_component(
        self, component: type[Component] | Component, /, *, immediate: bool = True
    ) -> Self:
        """
        Adds a component to the app. Can be used as a class decorator.

        Parameters
        ----------
        component: `type[Component] | Component`
            The component, or its `type`, to add. Will be instanced immediately if a `type` is passed.
        immediate: `bool`
            Whether to add (and instance, if it's a `type`) the component immediately or wait until `mainloop` is called and `entrypoint` is notified.

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

        def _add():
            self._components.append(component() if callable(component) else component)

        if immediate:
            _add()
        else:
            self.entrypoint += _add

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
            raise ValueError("Cannot remove internal component.")

        self._components.remove(component)  # type: ignore

    def get_component[T: Component](self, component: type[T] | str, /) -> T | None:
        """
        Gets a component from the app.

        Parameters
        ----------
        component: `type[Component] | str`
            The component's type's name, or the type itself. Will not be instanced.

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
        """
        Gets a list of components from the app.

        Parameters
        ----------
        component: `type[Component] | str`
            The component's type's name, or the type itself. Will not be instanced.

        Returns
        -------
        `list[Component] | None`
            The list of components, if found.
        """
        return list(
            filter(lambda c: c.__class__.__name__ == component, self._components)  # type: ignore
            if isinstance(component, str)
            else filter(lambda c: isinstance(c, component), self._components)  # type: ignore
        )

    def register_module(self, module: ModuleType, /) -> Self:
        """
        Registers a module to be initialized and cleaned up when the app is started and stopped.
        Useful for pygame modules such as freetype and mixer.\n
        Modules must have `init` and `quit` functions.

        Parameters
        ----------
        module: `ModuleType`
            The module to register.

        Returns
        -------
        `Self`
            The app, for chaining.

        Raises
        ------
        `ValueError`
            If the module doesn't have `init` and `quit` functions.
        """
        if not self._is_module_valid(module):
            raise ValueError("Module must have `init` and `quit` functions.")

        module.init()
        self.cleanup += module.quit

        return self

    def register_modules(self, /, *modules: ModuleType) -> Self:
        """
        Registers multiple modules to be initialized and cleaned up when the app is started and stopped.
        Useful for pygame modules such as freetype and mixer.\n
        Modules must have `init` and `quit` functions.

        Parameters
        ----------
        *modules: `ModuleType`
            The modules to register.

        Returns
        -------
        `Self`
            The app, for chaining.

        Raises
        ------
        `ValueError`
            If a module doesn't have `init` and `quit` functions.
        """

        for module in modules:
            self.register_module(module)

        return self

    def quit(self) -> None:
        """Closes the app in the next frame."""

        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _handle_possible_coroutine(
        self, func: Callable[[], Coroutine | None], /
    ) -> None:
        if isgeneratorfunction(func):
            self.executor.start_coroutine(func)
        else:
            func()

    def _is_module_valid(self, module: ModuleType, /) -> bool:
        return all(callable(getattr(module, c, False)) for c in ("init", "quit"))
