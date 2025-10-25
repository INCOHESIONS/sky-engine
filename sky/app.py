"""Contains the `App` class."""

from collections.abc import Iterator, Sequence
from cProfile import run as profile
from inspect import isgeneratorfunction
from typing import Callable, Protocol, Self

import pygame

from ._components import Chrono, Events, Executor, Keyboard, Mouse, Windowing
from .core import Component
from .hook import Hook
from .spec import AppSpec, WindowSpec
from .types import Coroutine
from .utils import callable_with_no_arguments, first, get_by_attrs, singleton
from .yieldable import Yieldable

__all__ = ["App"]


class _CompatibleModule(Protocol):
    def init(self) -> None: ...

    def quit(self) -> None: ...


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

    User-defined components can be added by subclassing `Component` and using the `add_component` method (or `component` as a class decorator).

    Hooks:
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

    def __init__(self, /, *, spec: AppSpec | WindowSpec | None = None) -> None:
        pygame.init()

        # probably bad practice but this does makes things real easy to use which is the whole point of this library
        Component.app = self
        Yieldable.app = self
        Hook.app = self

        self.spec = (
            AppSpec(window_spec=spec)
            if isinstance(spec, WindowSpec)
            else spec or AppSpec()
        )
        """The app's specification, i.e., pre-execution configuration."""

        self.entrypoint = Hook()
        """Executes before components are started up, just after `mainloop` is called."""

        self.setup = Hook()
        """Executes after components are started up, and before the first frame."""

        self.pre_update = Hook()
        """Executes before components are updated."""

        self.post_update = Hook()
        """Executes after components are updated."""

        self.teardown = Hook()
        """Executes before components are stopped, and after the last frame."""

        self.cleanup = Hook()
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

        self._internal_components: list[Component] = [
            self.events,
            self.mouse,
            self.keyboard,
            self.windowing,
            self.chrono,
            self.executor,
        ]  # do not change ordering

        self._components = self._internal_components.copy()

        self.is_running = True
        self.has_stopped = False

    def __contains__(self, component: type[Component] | Component, /) -> bool:
        """
        Checks if the app contains a component.\n
        If a type is passed, checks if the app contains any component of that type. Does not instance the type.

        Parameters
        ----------
        component: `type[Component] | Component`
            The component to check for.

        Returns
        -------
        `bool`
            Whether the app contains the component.
        """

        return self.has_component(component)

    def __iter__(self) -> Iterator[Component]:
        """
        Iterates over the app's components.

        Yields
        ------
        `Component`
            The next component.
        """

        yield from self._components

    @property
    def components(self) -> Sequence[Component]:
        """
        A copy of the app's components.

        Returns
        -------
        `Sequence[Component]`
            The components.
        """

        return self._components.copy()

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

        if self.spec.profile:
            profile("App()._mainloop()", sort="tottime")
        else:
            self._mainloop()

    def _mainloop(self) -> None:
        if self.has_stopped:
            raise RuntimeError("You cannot run this app instance again!")

        self.entrypoint.notify()

        for component in self._components:
            self._start_component(component)

        self.setup.notify()

        self.is_running = True

        while self.events.handle_events().lacks(pygame.QUIT):
            self.pre_update.notify()

            for component in self._components:
                component.update()

            self.post_update.notify()

        self.is_running = False
        self.has_stopped = True

        self.teardown.notify()

        for component in self._components:
            self._handle_possible_coroutine(component.stop)

        self.cleanup.notify()

        pygame.quit()

    run = mainloop  # alias
    __call__ = mainloop

    def add_component(
        self,
        component: type[Component] | Component,
        /,
        *,
        when: Hook | None = None,
    ) -> Self:
        """
        Adds a component to the app.\n
        Calls the component's `start` method if the app is running and the component hadn't yet been started.\n
        If you wish to use this as a class decorator, use `app.component` instead.

        Parameters
        ----------
        component: `type[Component] | Component`
            The component, or its `type`, to add. Will be instanced immediately if a `type` is passed.
        when: `Hook | None`, optional
            The Hook to use as a trigger for adding the component.
            If `None` (the default), the component will be added immediately.\n
            Basically a shorthand for `when += lambda: app.add_component(component)`.

        Returns
        -------
        Self
            The app, for chaining.

        Raises
        ------
        `ValueError`
            If a type is passed that cannot be instanced with no arguments or if the app has already stopped running.
        """

        if self.has_stopped:
            raise ValueError("The app has already stopped running!")

        if callable(component) and not callable_with_no_arguments(component):
            raise ValueError(
                f'Component types must have constructors that take no arguments to be passed in directly to `add_component` (problematic type: "{component.__name__}").'
            )

        def _add():
            self._components.append(
                comp := component() if callable(component) else component
            )

            if self.is_running and not getattr(comp, "_has_started", False):
                self._start_component(comp)

        if when is None:
            _add()
        else:
            when += _add

        return self

    def add_components(self, /, *components: type[Component] | Component) -> Self:
        """
        Adds multiple components to the app.

        Parameters
        ----------
        *components: `type[Component] | Component`
            The components, or their `type`, to add. Will be instanced immediately if a `type` is passed.

        Returns
        -------
        `Self`
            The app, for chaining.

        Raises
        ------
        `ValueError`
            If a type is passed that cannot be instanced with no arguments or if the app has already stopped running.
        """

        for component in components:
            self.add_component(component)

        return self

    def component[T: type[Component]](self, component: T, /) -> T:
        """
        Adds a component to the app.\n
        Must be used as the first decorator, and as such should come before others such as `@dataclass`.
        In constrast to `app.add_component`, this method will properly preserve the component's type.

        Examples
        --------
        ```python
        @app.component
        @dataclass
        class Player(Component):
            position: Vector2
        ```

        Parameters
        ----------
        component: `type[Component]`
            The type. Will be instanced immediately. Use `app.add_component` for finer control.

        Returns
        -------
        `T`
            The component, for chaining.

        Raises
        ------
        `ValueError`
            If the type passed cannot be instanced with no arguments or if the app has already stopped running.
        """
        self.add_component(component)
        return component

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
            If the component is internal or wasn't found.
        """

        if isinstance(component, type):
            component = self.get_component(component)  # pyright: ignore[reportAssignmentType]

        if component in self._internal_components:
            raise ValueError(
                f"Cannot remove internal component {component.__class__.__name__}."
            )

        self._components.remove(component)  # pyright: ignore[reportArgumentType]

    def clear_components(self):
        """Removes all non-internal components from the app."""

        self._components = self._internal_components.copy()

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

        return first(self.get_components(component), default=None)

    def get_components[T: Component](self, component: type[T] | str, /) -> list[T]:
        """
        Gets a list of components from the app.

        Parameters
        ----------
        component: `type[Component] | str`
            The component's type's name, or the type itself. Will not be instanced.

        Returns
        -------
        `list[Component]`
            The list of components, if found.
        """
        return list(
            filter(lambda c: c.__class__.__name__ == component, self._components)
            if isinstance(component, str)
            else filter(lambda c: isinstance(c, component), self._components)
        )  # pyright: ignore[reportReturnType]

    def has_component(self, component: type[Component] | Component, /) -> bool:
        """
        Checks if the app contains a component.\n
        If a type is passed, checks if the app contains any component of that type. Does not instance the type.

        Parameters
        ----------
        component: `type[Component] | Component`
            The component to check for.

        Returns
        -------
        `bool`
            Whether the app contains the component.
        """

        return (
            get_by_attrs(self._components, __class__=component) is not None
            if isinstance(component, type)
            else component in self._components
        )

    def register_module(
        self, module: _CompatibleModule, /, *, when: Hook | None = None
    ) -> Self:
        """
        Registers a module to be initialized and cleaned up when the app is started and stopped.
        Initializes the module immediately if `when` is None, otherwise initializes it when `when` is triggered.\n
        Modules must have `init` and `quit` functions.\n
        Useful for pygame modules such as `freetype` and `mixer`.

        Parameters
        ----------
        module: `_CompatibleModule`
            The module to register.
        when: `Hook | None`
            The Hook to use as a trigger for initializing the module.
            If `None` (the default), the module will be initialized immediately.\n

        Returns
        -------
        `Self`
            The app, for chaining.
        """

        if when is None:
            module.init()
        else:
            when += module.init

        self.cleanup += module.quit
        return self

    def register_modules(self, /, *modules: _CompatibleModule) -> Self:
        """
        Registers a module to be initialized and cleaned up when the app is started and stopped.
        Initializes the module immediately. Modules must have `init` and `quit` functions.\n
        Useful for pygame modules such as `freetype` and `mixer`.\n

        Parameters
        ----------
        *modules: `_CompatibleModule`
            The modules to register.

        Returns
        -------
        `Self`
            The app, for chaining.

        Raises
        ------
        `AssertionError`
            If the module does not have `init` and `quit` functions.
        """

        for module in modules:
            self.register_module(module)

        return self

    def quit(self) -> None:
        """Posts a `pygame.QUIT` event telling the app to close in the next frame."""

        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _handle_possible_coroutine(
        self, func: Callable[[], Coroutine | None], /
    ) -> None:
        if isgeneratorfunction(func):
            self.executor.start_coroutine(func)
        else:
            func()

    def _start_component(self, /, component: Component) -> None:
        self._handle_possible_coroutine(component.start)
        component._has_started = True  # pyright: ignore[reportAttributeAccessIssue]
