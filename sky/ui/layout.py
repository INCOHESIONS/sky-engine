"""Layouting functionality."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from dataclasses import KW_ONLY, dataclass
from typing import TYPE_CHECKING, Any, ClassVar, final, override

from ..hook import Hook
from ..utils import Rect, Vector2, walk_neighbours
from ..window import Window
from .core import UIElement

if TYPE_CHECKING:
    from ..app import App

__all__ = [
    "Flexbox",
    "flexbox",
    "FlexboxDescriptor",
    "Grid",
    "grid",
    "GridDescriptor",
    "Layout",
]


class LayoutDescriptor(ABC): ...


class Layout[TDescriptor: LayoutDescriptor = Any](ABC):
    """
    Base class for layout managers, objects responsible for the positioning and sizing of UI elements.
    Its elements can be added to the UI hierarchy by using the unpacking operator.

    Examples
    --------
    ```python
    from sky import App, Color, Vector2, WindowSpec
    from sky.colors import RED
    from sky.ui import Button, ButtonStyle, flexbox

    app = App()

    box = flexbox(
        position=Vector2(50, 50),
        size=app.window.size - Vector2(100, 100),
        elements=[Button(style=ButtonStyle()) for _ in range(10)],
    )

    app.ui.add_elements(*box)

    app.mainloop()
    ```
    """

    app: ClassVar[App] = None  # pyright: ignore[reportAssignmentType]

    def __init__(
        self,
        /,
        *,
        position: Vector2,
        size: Vector2,
        window: Window | None = None,
        elements: list[UIElement] | None = None,
        descriptor: TDescriptor | None = None,
    ) -> None:
        self._position = position
        self._size = size
        self._window = window or self.app.window
        self._elements = elements or []
        self._descriptor = descriptor

        self.on_composite = Hook()

        self.app.setup += self.composite

    def __iter__(self) -> Iterator[UIElement]:
        return iter(self._elements)

    def __contains__(self, element: UIElement, /) -> bool:
        return element in self._elements

    @property
    def elements(self) -> Sequence[UIElement]:
        """The layout's elements."""

        return self._elements.copy()

    @property
    def position(self) -> Vector2:
        """The layout's position."""

        return self._position

    @position.setter
    def position(self, value: Vector2, /) -> None:
        self._position = value
        self.composite()

    @property
    def size(self) -> Vector2:
        """The layout's size."""

        return self._size

    @size.setter
    def size(self, value: Vector2, /) -> None:
        self._size = value
        self.composite()

    @property
    def bounds(self) -> Rect:
        """The bounds of the layout."""

        return Rect(self.position, self.size)

    @bounds.setter
    def bounds(self, value: Rect, /) -> None:
        self.position = Vector2(value.topleft)
        self.size = Vector2(value.size)

    @final
    def add_element(self, element: UIElement, /, *, composite: bool = True) -> None:
        """Adds an element to the layout."""

        self._elements.append(element)
        element.on_any_change += self.composite

        if composite:
            self.composite()

    @final
    def remove_element(self, element: UIElement, /, *, composite: bool = True) -> None:
        """Removes an element from the layout."""

        self._elements.remove(element)
        element.on_any_change -= self.composite

        if composite:
            self.composite()

    @final
    def clear_elements(self, *, composite: bool = True) -> None:
        """Removes all elements from the layout."""

        for element in self._elements:
            self.remove_element(element, composite=False)

        if composite:
            self.composite()

    def composite(self) -> None:
        """Recomputes the bounds of each element in the layout, calling `calculate` for each element."""

        for prev, element, next in walk_neighbours(self._elements):
            element.bounds = self.calculate(element, prev, next)

        self.on_composite.notify()

    @abstractmethod
    def calculate(
        self,
        element: UIElement,
        previous_element: UIElement | None,
        next_element: UIElement | None,
        /,
    ) -> Rect:
        """Calculates the bounds of a single element based."""

        raise NotImplementedError()


@final
@dataclass
class FlexboxDescriptor(LayoutDescriptor):
    """Extra data for the `Flexbox` layout."""

    _: KW_ONLY

    gap: float = 15
    padding: float = 15


@final
class Flexbox(Layout[FlexboxDescriptor]):
    """
    The flexbox layout separates each element by a `gap`,
    keeping them at a distance of `padding` from the edges of the bounds of the layout.\n
    Organizes the elements in a way so as to minimize negative space, automatically figuring out the best number of rows and columns.
    """

    @override
    def calculate(
        self,
        element: UIElement,
        previous_element: UIElement | None,
        next_element: UIElement | None,
        /,
    ) -> Rect:
        raise NotImplementedError()  # TODO:


@final
@dataclass
class GridDescriptor(LayoutDescriptor):
    """Extra data for the `Grid` layout."""

    _: KW_ONLY

    rows: int = 1
    columns: int = 1
    gap: float = 15
    padding: float = 15


@final
class Grid(Layout[GridDescriptor]):
    """
    The grid layout separates each element by a `gap`,
    keeping them at a distance of `padding` from the edges of the bounds of the layout.\n
    Organizes them in a fixed number of rows and columns.
    """

    @override
    def calculate(
        self,
        element: UIElement,
        previous_element: UIElement | None,
        next_element: UIElement | None,
        /,
    ) -> Rect:
        raise NotImplementedError()  # TODO:


def flexbox(
    *,
    position: Vector2,
    size: Vector2,
    window: Window | None = None,
    elements: list[UIElement] | None = None,
    gap: float = 15,
    padding: float = 15,
) -> Flexbox:
    """Utility method for creating a flexbox layout without having to directly interact with the layout descriptor."""

    return Flexbox(
        position=position,
        size=size,
        window=window,
        elements=elements,
        descriptor=FlexboxDescriptor(
            gap=gap,
            padding=padding,
        ),
    )


def grid(
    *,
    position: Vector2,
    size: Vector2,
    window: Window | None = None,
    elements: list[UIElement] | None = None,
    rows: int = 1,
    columns: int = 1,
    gap: float = 15,
    padding: float = 15,
) -> Grid:
    """Utility method for creating a grid layout without having to directly interact with the layout descriptor."""

    return Grid(
        position=position,
        size=size,
        window=window,
        elements=elements,
        descriptor=GridDescriptor(
            rows=rows,
            columns=columns,
            gap=gap,
            padding=padding,
        ),
    )
