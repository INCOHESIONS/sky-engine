from typing import Self

import pygame

from sky.listenable import Listenable

from .components import Chrono, Events, Keyboard, Mouse, Windowing
from .core import Component, singleton
from .spec import AppSpec
from .utils import first, get_by_attrs

__all__ = ["App"]


@singleton
class App:
    def __init__(self, /, *, spec: AppSpec = AppSpec()) -> None:
        pygame.init()

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

        self._components: list[Component] = [
            self.events,
            self.keyboard,
            self.mouse,
            self.windowing,
            self.chrono,
        ]  # do not change ordering

        for component in self._components:
            component._internal = True  # type: ignore

    def mainloop(self) -> None:
        for component in self._components:
            component.start()

        self.setup.notify()

        while not self._should_quit():
            self.events._events = pygame.event.get()  # type: ignore

            self.pre_update.notify()

            for component in self._components:
                component.update()

            self.post_update.notify()

        self.teardown.notify()

        for component in self._components:
            component.stop()

        pygame.quit()

    run = mainloop

    def add_component(self, component: type[Component] | Component, /) -> Self:
        self._components.append(
            component() if isinstance(component, type) else component
        )
        return self

    def remove_component(self, component: type[Component] | Component, /) -> None:
        if getattr(component, "_internal", False):
            raise ValueError("Cannot remove internal component")

        if isinstance(component, type):
            self._components.remove(
                first(filter(lambda c: isinstance(c, component), self._components))  # type: ignore
            )
            return

        self._components.remove(component)

    def quit(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _should_quit(self) -> bool:
        return get_by_attrs(self.events, type=pygame.QUIT) is not None
