"""Contains the `App` class."""

from collections.abc import Iterator, Sequence
from cProfile import run as profile
from typing import Literal, Protocol, Self, final

import pygame

from ._services import Chrono, Events, Executor, Keyboard, Mouse, Windowing
from .core import Component, Service
from .hook import Hook
from .scene import Scene
from .spec import AppSpec, SceneSpec, WindowSpec
from .utils import callable_with_no_arguments, singleton
from .window import Window
from .yieldable import Yieldable

__all__ = ["App"]


@final
class _CompatibleModule(Protocol):
    def init(self) -> None: ...

    def quit(self) -> None: ...


@singleton
class App:
    """
    The singleton `App` class. Pre-execution configuration is defined with `AppSpec`, such as the main window's title and size.\n
    User-defined `Component`s can be added by subclassing `Component` and using the `add_component` method on the `App` (which will add them to the main scene), or on a specific `Scene`.\n
    Services can also be added by subclassing `Service` and using the `add_service` method.

    ### Order of execution:
        ```
        Pre-loop:
            1. App.preload
            2. Service.start (for all services)
            3. Scene.start (for all scenes)
                1. Scene.pre_start
                2. Component.start
                3. Scene.post_start
            4. App.setup

        During loop:
            1. App.pre_update
            2. Service.update (for all services)
            3. Scene.update (for all scenes)
                1. Scene.pre_update
                2. Component.update
                3. Scene.post_update
            4. App.post_update

        Post-loop:
            1. App.teardown
            2. Service.stop (for all services)
            3. Scene.stop (for all scenes)
                1. Scene.pre_stop
                2. Component.stop
                3. Scene.post_stop
            4. App.cleanup
        ```

    ### Services (in order of execution):
        - `Events` (handles pygame events)
        - `Keyboard` (handles keyboard input)
        - `Mouse` (handles mouse input)
        - `Windowing` (handles windowing)
        - `Chrono` (handles time)
        - `Executor` (handles coroutines)

    Parameters
    ----------
    spec: `AppSpec | WindowSpec | SceneSpec | None`, optional
        Specification for the whole app, just the main scene, or just the main window.
        By default `None`, which creates a default `AppSpec`. See `AppSpec` for more information.
    modules: `Sequence[_CompatibleModule] | None`, optional
        A `Sequence` of objects that have `init` and `quit` methods, such as the `pygame.freetype` or `pygame.mixer` modules, to register.
        Modules will be initialized (`init`) immediately, and cleaned up (`quit`) when the `App`'s `cleanup` `Hook` is notified.
        By default `None`.
    """

    def __init__(
        self,
        /,
        *,
        spec: AppSpec | WindowSpec | SceneSpec | None = None,
        modules: Sequence[_CompatibleModule] | None = None,
    ) -> None:
        pygame.init()

        # probably bad practice but this does makes things real easy to use which is the whole point of this library
        Component.app = self
        Yieldable.app = self
        Scene.app = self
        Hook.app = self

        self.is_running = False

        self.spec = (
            AppSpec(window_spec=spec)
            if isinstance(spec, WindowSpec)
            else AppSpec(scene_spec=spec)
            if isinstance(spec, SceneSpec)
            else spec or AppSpec()
        )
        """The app's specification, i.e., pre-execution configuration."""

        self.preload = Hook()
        """Executes before scenes and services are started up, just after mainloop is called."""

        self.setup = Hook()
        """Executes after scenes and services are started up, and before the first frame."""

        self.pre_update = Hook()
        """Executes before scenes and services are updated."""

        self.post_update = Hook()
        """Executes after scenes and services are updated."""

        self.teardown = Hook()
        """Executes before scenes and services are stopped, and after the last frame."""

        self.cleanup = Hook()
        """Executes after scenes and services are stopped, and before the app is destroyed; cleans up registered modules."""

        for module in modules or []:
            module.init()
            self.cleanup += module.quit

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

        self._internal_services: list[Service] = [
            self.events,
            self.mouse,
            self.keyboard,
            self.windowing,
            self.chrono,
            self.executor,
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
    def window(self) -> Window:
        """
        Short for `app.windowing.main_window`.

        Returns
        -------
        `Window`
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

        # Order of execution:
            ```
            Pre-loop:
                1. App.preload
                2. Service.start (for all services)
                3. Scene.start (for all scenes)
                    1. Scene.pre_start
                    2. Component.start
                    3. Scene.post_start
                4. App.setup

            During loop:
                1. App.pre_update
                2. Service.update (for all services)
                3. Scene.update (for all scenes)
                    1. Scene.pre_update
                    2. Component.update
                    3. Scene.post_update
                4. App.post_update

            Post-loop:
                1. App.teardown
                2. Service.stop (for all services)
                3. Scene.stop (for all scenes)
                    1. Scene.pre_stop
                    2. Component.stop
                    3. Scene.post_stop
                4. App.cleanup
            ```
        """

        if self.spec.profile:
            profile("App()._mainloop()", sort="tottime")
        else:
            self._mainloop()

    def _mainloop(self) -> None:
        self.preload.notify()

        for service in self.services:
            service.start()

        for scene in self.scenes:
            scene.start()

        self.setup.notify()

        self.is_running = True

        while self.events.handle_events().lacks(pygame.QUIT):
            self.pre_update.notify()

            for service in self.services:
                service.update()

            for scene in self.scenes:
                scene.update()

            self.post_update.notify()

        self.is_running = False

        self.teardown.notify()

        for service in self.services:
            service.stop()

        for scene in self.scenes:
            scene.stop()

        self.cleanup.notify()

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
        Adds a scene to the app's scenes.\n
        If a type is passed, it will be instanced immediately with no arguments.

        Parameters
        ----------
        scene: `type[Scene] | Scene`
            The scene, or its type (to be instanced), to add.
        mode: `Literal["add", "replace_all", "replace_last"]`
            The mode of loading the scene.
            "add" appends the scene to the list of scenes.
            "replace_all" removes all scenes and leaves the new scene as the only scene.
            "replace_last" replaces the last scene with the new scene.

        Raises
        ------
        ValueError
            If the `Scene`'s type is passed and it cannot be instanced with no arguments.
        """

        if isinstance(scene, type):
            if callable_with_no_arguments(scene):
                scene = scene()
            else:
                raise ValueError("Scene cannot be instanced with no arguments.")

        match mode:
            case "add":
                self._scenes.append(scene)
            case "replace_all":
                for scene in self.scenes:
                    self.unload_scene(scene)

                self._scenes = [scene]
            case "replace_last":
                try:
                    self.unload_scene(self.scenes[-1])
                except IndexError:
                    pass

                self._scenes.append(scene)

        if self.is_running and not scene.is_running:
            scene.start()

    def unload_scene(self, scene: Scene, /):
        """
        Removes a `Scene` from the list of scenes and stops it.

        Parameters
        ----------
        scene: `Scene`
            The scene to unload.
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
        Adds a component to the `Scene`.\n
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
        """

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
        ValueError
            If the service is an internal service or if the service is not registered.
        """

        if service in self._internal_services:
            raise ValueError("Cannot remove internal service")

        self._services.remove(service)
        return self

    def quit(self) -> None:
        """Posts a `pygame.QUIT` event telling the app to close in the next frame."""

        self.events.post(pygame.QUIT)
