from bisect import insort
from collections.abc import Iterator
from typing import final, override

from ..core import Service, State
from ..hook import Hook
from ..ui import Layout, UIElement

__all__ = ["UI"]


@final
class UI(Service):
    def __init__(self) -> None:
        UIElement.app = self.app
        Layout.app = self.app

        self._elements: list[UIElement] = []
        self._interacting: UIElement | None = None

        self.on_interact = Hook()

    def __iter__(self) -> Iterator[UIElement]:
        return iter(self._elements)

    def __contains__(self, element: UIElement, /) -> bool:
        return element in self._elements

    @property
    def interacting(self) -> UIElement | None:
        """The element currently being interacted with."""

        return self._interacting

    @override
    def update(self) -> None:
        old_interacting = self._interacting
        self._interacting = None

        for element in self._elements:
            if element.calculate_state() != State.none:
                self._interacting = element

        if self._interacting != old_interacting and self._interacting:
            self.on_interact.notify()

        for element in self._elements:
            element.update()
            element.render()

    def add_element(self, element: UIElement, /) -> None:
        """Adds an element to the UI."""

        insort(self._elements, element, key=lambda x: -x.layer)

    def add_elements(self, /, *elements: UIElement) -> None:
        """Adds multiple elements to the UI."""

        for element in elements:
            self.add_element(element)

    def remove_element(self, element: UIElement, /) -> None:
        """Removes an element from the UI."""

        self._elements.remove(element)

    def clear_elements(self) -> None:
        """Clears all elements from the UI."""

        for element in self._elements:
            self.remove_element(element)
