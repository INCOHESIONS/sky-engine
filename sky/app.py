"""Contains the `App` class."""

from collections.abc import Iterator, Sequence
from cProfile import run as profile
from itertools import chain as flatten
from typing import Literal, Self

import pygame

from ._services import UI, Chrono, Events, Executor, Keyboard, Mouse, Windowing
from .core import Component, Service
from .hook import Hook
from .scene import Scene
from .spec import AppSpec, SceneSpec, WindowSpec
from .utils import attempt_empty_call, singleton
from .window import Window
from .yieldable import Yieldable

__all__ = ["App"]


@singleton
class App:
    """
    The singleton `App` class. Pre-execution configuration is defined with `AppSpec`, such as the main window's title and size.\n
    User-defined `Component`s can be added by subclassing `Component` and using the `add_component` method on the `App` (which will add them to the main scene), or on a specific `Scene`.\n
    Services can also be added by subclassing `Service` and using the `add_service` method.

    # Order of execution:
        - Pre-loop:
            1. `App.preload`
            2. `Service.start` (for all services)
            3. `Scene.start` (for all scenes)
                1. `Scene.pre_start`
                2. `Component.start`
                3. `Scene.post_start`
            4. `App.setup`

        - During loop:
            1. `App.pre_update`
            2. `Service.update` (for all services)
            3. `Scene.update` (for all scenes)
                1. `Scene.pre_update`
                2. `Component.update`
                3. `Scene.post_update`
            4. `App.post_update`

        - Post-loop:
            1. `App.teardown`
            2. `Service.stop` (for all services)
            3. `Scene.stop` (for all scenes)
                1. `Scene.pre_stop`
                2. `Component.stop`
                3. `Scene.post_stop`
            4. `App.cleanup`

    # Services (in order of execution):
        - `Events` (handles `pygame` events)
        - `Keyboard` (handles keyboard input)
        - `Mouse` (handles mouse input)
        - `Windowing` (handles windowing)
        - `Chrono` (handles time-related data)
        - `Executor` (handles coroutines)
        - `UI` (handles the user interface, WIP)

    Constructor Parameters
    ----------------------
    spec: `AppSpec | WindowSpec | SceneSpec | None`, optional
        Specification for the whole app, just the main scene, or just the main window.
        By default `None`, which creates a default `AppSpec`. See `AppSpec` for more information.
    """

    def __init__(
        self,
        /,
        *,
        spec: AppSpec | WindowSpec | SceneSpec | None = None,
    ) -> None:
        """
        App constructor.

        Parameters
        ----------
        spec: `AppSpec | WindowSpec | SceneSpec | None`, optional
            Specification for the whole app, just the main scene, or just the main window.
            By default `None`, which creates a default `AppSpec`. See `AppSpec` for more information.
        """

        pygame.init()

        self._handle_references()

        self.is_running = False

        self.spec = (
            AppSpec(window_spec=spec)
            if isinstance(spec, WindowSpec)
            else AppSpec(scene_spec=spec)
            if isinstance(spec, SceneSpec)
            else spec or AppSpec()
        )
        """The app's specification, i.e., pre-execution configuration."""

        self.on_preload = Hook()
        """Executes before scenes and services are started up, just after mainloop is called."""

        self.on_setup = Hook()
        """Executes after scenes and services are started up, and before the first frame."""

        self.pre_update = Hook()
        """Executes before scenes and services are updated."""

        self.post_update = Hook()
        """Executes after scenes and services are updated."""

        self.on_teardown = Hook()
        """Executes before scenes and services are stopped, and after the last frame."""

        self.on_cleanup = Hook()
        """Executes after scenes and services are stopped, and before the app is destroyed; cleans up registered modules."""

        for module in self.spec.modules:
            module.init()
            self.on_cleanup += module.quit

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
        """Handles `Coroutine`s."""

        self.ui = UI()
        """Handles `UIElement`s."""

        self._internal_services: list[Service] = [
            self.events,
            self.mouse,
            self.keyboard,
            self.windowing,
            self.chrono,
            self.executor,
            self.ui,
        ]  # do not change ordering

        self._services = self._internal_services.copy()

        self._scenes: list[Scene] = []

        if self.spec.scene_spec:
            self.load_scene(Scene(spec=self.spec.scene_spec))

    def __iter__(self) -> Iterator[Scene]:
        """
        Iterates over the app's scenes.

        Yields
        ------
        `Scene`
            The next scene.
        """

        yield from self._scenes

    def __bool__(self) -> bool:
        return bool(self._scenes)

    @property
    def services(self) -> Sequence[Service]:
        """The app's services."""

        return self._services.copy()

    @property
    def scenes(self) -> Sequence[Scene]:
        """The app's scenes."""

        return self._scenes.copy()

    @property
    def scene(self) -> Scene:
        """
        The app's main scene. Always the last scene in the list.

        Raises
        ------
        `IndexError`
            If there are no scenes.
        """

        return self._scenes[-1]

    @property
    def all_components(self) -> Sequence[Component]:
        """All components, in all currently loaded scenes."""

        return list(flatten(*(scene.components for scene in self._scenes)))

    @property
    def window(self) -> Window:
        """
        Short for `app.windowing.main_window`, but with its being non-optional for ease of use.

        Returns
        -------
        `Window`
            The main window.

        Raises
        ------
        `AssertionError`
            If the main window is not set (i.e. no windows are open due to the app being in headless mode).
        """

        assert self.windowing.main_window is not None
        return self.windowing.main_window

    @property
    def on_render(self) -> Hook:
        """
        Alias for `app.window.on_render`.

        Returns
        -------
        `Hook[[], None]`
            The hook.

        Raises
        ------
        `AssertionError`
            If the main window is not set (i.e. no windows are open due to the app being in headless mode).
        """

        return self.window.on_render

    def mainloop(self) -> None:
        """The app's main loop. See `App`'s documentation for more other information."""

        if self.spec.profile:
            profile("App()._mainloop()", sort="tottime")
        else:
            self._mainloop()

    def _mainloop(self) -> None:
        self.on_preload.notify()

        for service in self.services:
            service.start()

        for scene in self.scenes:
            scene.start()

        self.on_setup.notify()

        self.is_running = True

        while self.events.handle_events().lacks(pygame.QUIT):
            self.pre_update.notify()

            for service in self.services:
                service.update()

            for scene in self.scenes:
                scene.update()

            self.post_update.notify()

        self.is_running = False

        self.on_teardown.notify()

        for service in self.services:
            service.stop()

        for scene in self.scenes:
            scene.stop()

        self.on_cleanup.notify()

        pygame.quit()

    run = mainloop  # alias
    __call__ = mainloop

    def load_scene(
        self,
        scene: type[Scene] | Scene,
        /,
        *,
        mode: Literal["add", "replace_all", "replace_last"] = "add",
    ) -> None:
        """
        Adds a scene to the app's scene list and starts it.\n
        If a type is passed, it will be instanced immediately with no arguments.

        Parameters
        ----------
        scene: `type[Scene] | Scene`
            The scene, or its type (to be instanced), to add.
        mode: `Literal["add", "replace_all", "replace_last"]`
            The mode of loading the scene.
            - "add" appends the scene to the list of scenes.
            - "replace_all" removes all scenes and leaves the new scene as the only scene.
            - "replace_last" replaces the last scene with the new scene.

        Raises
        ------
        `ValueError`
            If the `Scene`'s type is passed and it cannot be instanced with no arguments.

        `RuntimeError`
            If the scene is already loaded and running.
        """

        if isinstance(scene, type):
            scene = attempt_empty_call(
                scene, message="Scene cannot be instanced with no arguments."
            )

        match mode:
            case "add":
                ...
            case "replace_all":
                for scene in self.scenes:
                    self.unload_scene(scene)
            case "replace_last":
                if self.scenes:
                    self.unload_scene(self.scenes[-1])

        self._scenes.append(scene)

        if self.is_running:
            scene.start()

    def unload_scene(self, scene: Scene, /):
        """
        Removes a `Scene` from the list of scenes and stops it.

        Parameters
        ----------
        scene: `Scene`
            The scene to unload.

        Raises
        ------
        `ValueError`
            If the scene is not present in the list of scenes.

        `RuntimeError`
            If the scene was not loaded and running.
        """

        self._scenes.remove(scene)
        scene.stop()

    def toggle_scene(self, scene: Scene, /):
        """
        Loads a `Scene` if it's not already loaded, or unloads it if it is.

        Parameters
        ----------
        scene: `Scene`
            The scene to toggle.
        """

        if scene in self._scenes:
            self.unload_scene(scene)
        else:
            self.load_scene(scene)

    def add_component(self, component: type[Component] | Component, /) -> Self:
        """
        Adds a component to the current `Scene`.\n
        Calls the component's `start` method if it hasn't yet been started.

        Parameters
        ----------
        component: `type[Component] | Component`
            The component, or its `type`, to add. Will be instanced immediately if a `type` is passed.

        Returns
        -------
        `Self`
            The `App`, for chaining.

        Raises
        ------
        `ValueError`
            If a type is passed that cannot be instanced with no arguments.
        """

        self.scene.add_component(component)
        return self

    def add_components(self, /, *components: type[Component] | Component) -> Self:
        """
        Adds a component to the current `Scene`.\n
        Calls the component's `start` method if it hasn't yet been started.

        Parameters
        ----------
        *components: `type[Component] | Component`
            The components, or their `type`, to add. Will be instanced immediately if a `type` is passed.

        Returns
        -------
        `Self`
            The `App`, for chaining.

        Raises
        ------
        `ValueError`
            If a type is passed that cannot be instanced with no arguments or if the `Scene` has already stopped running.
        """

        for component in components:
            self.add_component(component)

        return self

    def remove_component(self, component: type[Component] | Component, /) -> None:
        """
        Removes a component from the main `Scene`.

        Parameters
        ----------
        component: `type[Component] | Component`
            The component, or its type, to remove. Will try and find a component of matching type if a type is passed. That type will not be instanced.

        Raises
        ------
        `ValueError`
            If the component wasn't found.
        """

        self.scene.remove_component(component)

    def clear_components(self):
        """Removes all components from the main `Scene`."""

        for component in self.scene.components:
            self.remove_component(component)

    def singleton_component[C: type[Component]](self, cls: C, /) -> C:
        """
        Instantiates and adds the instance of the decorated `Component` to the current `Scene` immediately.\n
        Also makes the decorated class a `Singleton`.

        Parameters
        ----------
        component: `C`
            The type to instantiate. Must be a subclass of `Component`.

        Returns
        -------
        `C`
            The original type.
        """

        return singleton(self.immediate_component(cls))

    def immediate_component[C: type[Component]](self, cls: C, /) -> C:
        """
        Instantiates and adds the instance of the decorated `Component` to the current `Scene` immediately.

        Parameters
        ----------
        component: `C`
            The type to instantiate. Must be a subclass of `Component`.

        Returns
        -------
        `C`
            The original type.
        """

        self.add_component(cls)

        return cls

    def get_component[T: Component](self, component: type[T] | str, /) -> T | None:
        """
        Gets a component from the current `Scene`.

        Parameters
        ----------
        component: `type[Component] | str`
            The component's type's name, or the type itself. Will not be instanced.

        Returns
        -------
        `Component | None`
            The component, if found.
        """

        return self.scene.get_component(component)

    def get_components[T: Component](self, component: type[T] | str, /) -> Sequence[T]:
        """
        Gets a collection of components from the current `Scene`.

        Parameters
        ----------
        component: `type[Component] | str`
            The component's type's name, or the type itself. Will not be instanced.

        Returns
        -------
        `Sequence[Component]`
            The collection of components, if found.
        """

        return self.scene.get_components(component)

    def add_service(self, service: Service, /) -> Self:
        """
        Adds a service to the app.

        Parameters
        ----------
        service: `Service`
            The service to add.

        Returns
        -------
        `Self`
            The app, for chaining.

        Raises
        ------
        `ValueError`
            If the service already exists.
        """

        if service in self._services:
            raise ValueError("Service already exists!")

        self._services.append(service)
        return self

    def remove_service(self, service: Service, /) -> Self:
        """
        Removes a service from the app.

        Parameters
        ----------
        service: `Service`
            The service to remove.

        Returns
        -------
        `Self`
            The app, for chaining.

        Raises
        ------
        `ValueError`
            If the service is an internal service or if the service is not registered.
        """

        if service in self._internal_services:
            raise ValueError("Cannot remove internal service")

        self._services.remove(service)
        return self

    def quit(self) -> None:
        """Posts a `pygame.QUIT` event, telling the app to close the next frame."""

        self.events.post(pygame.QUIT)

    # probably bad practice but this makes things real easy to use which is the whole point of this library
    def _handle_references(self) -> None:
        Component.app = self
        Yieldable.app = self
        Scene.app = self
        Hook.app = self
