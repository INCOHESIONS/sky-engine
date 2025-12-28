"""Contains the `Scene` class, used for managing components."""

from collections.abc import Iterator, Sequence
from inspect import isgeneratorfunction
from typing import TYPE_CHECKING, Callable, ClassVar, Self, final

from .core import Component
from .hook import Hook
from .spec import SceneSpec
from .types import Coroutine
from .utils import filterl, first, is_callable_with_no_arguments

if TYPE_CHECKING:
    from .app import App


__all__ = ["Scene"]


class Scene:
    """
    A collection of `Component`s for ease of management.\n
    Note that `Scene`s can be started and stopped multiple times, and their `start` and `stop` methods will be called each time.

    Hooks:
        ```
        Pre-loop:
            pre_start (before components are started)
            post_start (after components are started)

        During loop:
            pre_update (before components are updated)
            post_update (after components are updated)

        Post-loop:
            pre_stop (before components are stopped)
            post_stop (after components are stopped)
        ```
    """

    app: ClassVar[App] = None  # pyright: ignore[reportAssignmentType]

    def __init__(self, /, *, spec: SceneSpec | None = None):
        self.spec = spec if isinstance(spec, SceneSpec) else SceneSpec()

        self._components = self.spec.components

        self.pre_start = Hook()
        self.post_start = Hook()

        self.pre_update = Hook()
        self.post_update = Hook()

        self.pre_stop = Hook()
        self.post_stop = Hook()

        self.is_running = False

    def __post_init__(self) -> None:
        """@dataclass support."""

        for base in self.__class__.__bases__:
            base.__init__(self)

    def __contains__(self, component: type[Component] | Component, /) -> bool:
        return self.has_component(component)

    def __iter__(self) -> Iterator[Component]:
        yield from self._components

    def __bool__(self) -> bool:
        return bool(self._components)

    @final
    @property
    def components(self) -> Sequence[Component]:
        """Returns a sequence of all components in this `Scene`."""

        return self._components.copy()

    @final
    @classmethod
    def from_components(cls, components: list[Component], /) -> Self:
        """
        Creates a new `Scene` from a sequence of components.

        Parameters
        ----------
        components: `Iterable[Component]`
            The components to add to the scene.

        Returns
        -------
        `Scene`
            The new `Scene`.
        """

        return cls(spec=SceneSpec(components=components))

    def start(self):
        """
        Starts this `Scene` and all of its components.

        Raises
        ------
        RuntimeError
            If the scene is already running.
        """

        if self.is_running:
            raise RuntimeError("A Scene cannot be started when it's already running!")

        self.pre_start.notify()

        for component in self._components:
            self._start_component(component)

        self.post_start.notify()

        self.is_running = True

    def update(self):
        """
        Updates this `Scene` and all of its components.

        Raises
        ------
        RuntimeError
            If the scene is not running.
        """

        if not self.is_running:
            raise RuntimeError("A Scene cannot be updated when it's not running!")

        self.pre_update.notify()

        for component in self._components:
            component.update()

        self.post_update.notify()

    def stop(self):
        """
        Stops this `Scene` and all of its components.

        Raises
        ------
        RuntimeError
            If the scene is not running.
        """

        if not self.is_running:
            raise RuntimeError("A Scene cannot be stopped when it's not running!")

        self.pre_stop.notify()

        for component in self._components:
            if not getattr(component, "_has_stopped", False):
                component.stop()

        self.post_stop.notify()

        self.is_running = False

    def add_component(
        self,
        component: type[Component] | Component,
        /,
        *,
        when: Hook | None = None,
    ) -> Self:
        """
        Adds a component to the `Scene`.\n
        Calls the component's `start` method if it hasn't yet been started.

        Parameters
        ----------
        component: `type[Component] | Component`
            The component, or its `type`, to add. Will be instanced immediately if a `type` is passed.
        when: `Hook | None`, optional
            The `Hook` to use as a trigger for adding the component.
            Will remove the callback from the `Hook` once the component has been added.\n
            If `None` (the default), the component will be added immediately instead.

        Returns
        -------
        Self
            The `Scene`, for chaining.

        Raises
        ------
        `ValueError`
            If a type is passed that cannot be instanced with no arguments.
        """

        # `is_callable_with_no_arguments` for an immediate error instead of `attempt_empty_call`; better than erroring on `when`
        if callable(component) and not is_callable_with_no_arguments(component):
            raise ValueError(
                f"{component.__name__} cannot be instanced with no arguments!"
            )

        def _add():
            nonlocal when

            self._components.append(
                comp := component() if callable(component) else component
            )

            if not getattr(comp, "_has_started", False):
                self._start_component(comp)

            if when:
                when -= _add

        if when is None:
            _add()
        else:
            when += _add

        return self

    def add_components(self, /, *components: type[Component] | Component) -> Self:
        """
        Adds multiple components to the `Scene`.

        Parameters
        ----------
        *components: `type[Component] | Component`
            The components, or their `type`, to add. Will be instanced immediately if a `type` is passed.

        Returns
        -------
        `Self`
            The `Scene`, for chaining.

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
        Removes a component from the `Scene`. Also calls its `stop` method.

        Parameters
        ----------
        component: `type[Component] | Component`
            The component, or its type, to remove. Will try and find a component of matching type if a type is passed. That type will not be instanced.

        Raises
        ------
        `ValueError`
            If the component wasn't found.
        """

        comp = (
            self.get_component(component) if isinstance(component, type) else component
        )

        if comp is None:
            raise ValueError("Component not found.")

        self._components.remove(comp)

        if not getattr(comp, "_has_stopped", False):
            comp.stop()

    def clear_components(self):
        """Removes all components from the `Scene`."""

        for component in self._components:
            self.remove_component(component)

    def get_component[T: Component](self, component: type[T] | str, /) -> T | None:
        """
        Gets a component from the `Scene`.

        Parameters
        ----------
        component: `type[Component] | str`
            The component's type's name, or the type itself. Will not be instanced.

        Returns
        -------
        `Component | None`
            The component, if found.
        """

        return first(self.get_components(component))

    def get_components[T: Component](self, component: type[T] | str, /) -> Sequence[T]:
        """
        Gets a collection of components from the `Scene`.

        Parameters
        ----------
        component: `type[Component] | str`
            The component's type's name, or the type itself. Will not be instanced.

        Returns
        -------
        `Sequence[Component]`
            The collection of components, if found.
        """

        return filterl(
            (lambda c: c.__class__.__name__ == component)
            if isinstance(component, str)
            else lambda c: isinstance(c, component),
            self._components,
        )  # pyright: ignore[reportReturnType]

    def has_component(self, component: type[Component] | Component | str, /) -> bool:
        """
        Checks if the `Scene` contains a component.\n
        If a type is passed, checks if the `Scene` contains any component of that type. Does not instance the type.\n
        If a string is passed, checks if the `Scene` contains any component with a matching type name.

        Parameters
        ----------
        component: `type[Component] | Component | str`
            The `Component`, its type, or the name of its type to check for.

        Returns
        -------
        `bool`
            Whether the `Scene` contains the component.
        """

        return (
            self.get_component(
                component.__class__ if isinstance(component, Component) else component
            )
            is not None
        )

    @final
    def _start_component(self, /, component: Component) -> None:
        self._handle_possible_coroutine(component.start)
        component._has_started = True  # pyright: ignore[reportAttributeAccessIssue]

    @final
    def _stop_component(self, /, component: Component) -> None:
        self._handle_possible_coroutine(component.start)
        component._has_stopped = True  # pyright: ignore[reportAttributeAccessIssue]

    @final
    def _handle_possible_coroutine(
        self, func: Callable[[], Coroutine | None], /
    ) -> None:
        if isgeneratorfunction(func):
            self.app.executor.start_coroutine(func)
        else:
            func()
