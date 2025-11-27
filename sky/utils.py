"""Utilities, and extensions of `pygame` classes that replace certain methods with expection-less versions for ease of use."""

from collections.abc import Generator, Iterable, Iterator, Sequence
from inspect import Parameter, signature
from random import randint, uniform
from typing import Any, Callable, Self, override

from pygame import Color as PygameColor
from pygame import Rect as PygameRect
from pygame import Vector2 as PygameVector2
from pygame import Vector3 as PygameVector3
from pygame.typing import SequenceLike
from singleton_decorator import (  # pyright: ignore[reportMissingTypeStubs]
    singleton as untyped_singleton,  # pyright: ignore[reportUnknownVariableType]
)

from .easing import linear

__all__ = [
    "animate",
    "clamp",
    "Color",
    "filter_by_attrs",
    "filterl",
    "first",
    "get_by_attrs",
    "ilen",
    "is_callable_with_no_arguments",
    "last",
    "mapl",
    "Rect",
    "saturate",
    "singleton",
    "Vector2",
    "Vector3",
    "walk_neighbours",
]


class Vector2(PygameVector2):
    """Replacement for `pygame.Vector2` with some extra utilities and exception-less versions of common methods."""

    @classmethod
    def zero(cls) -> Self:
        """Returns a zero `Vector2`. Same as `Vector2()`"""

        return cls(0, 0)

    @classmethod
    def one(cls) -> Self:
        """Returns a `Vector2` with all components set to 1."""

        return cls(1, 1)

    @classmethod
    def up(cls) -> Self:
        """Returns a `Vector2` pointing upwards."""

        return cls(0, -1)

    @classmethod
    def down(cls) -> Self:
        """Returns a `Vector2` pointing downwards."""

        return cls(0, 1)

    @classmethod
    def left(cls) -> Self:
        """Returns a `Vector2` pointing left."""

        return cls(-1, 0)

    @classmethod
    def right(cls) -> Self:
        """Returns a `Vector2` pointing right."""

        return cls(1, 0)

    @classmethod
    def random(cls) -> Self:
        """Returns a `Vector2` pointing in a random direction."""

        return cls(uniform(-1, 1), uniform(-1, 1)).normalize()

    @override
    def normalize(self) -> Self:
        """
        Normalizes the vector.\n
        Exception-less version of `pygame.Vector2.normalize`.

        Returns
        -------
        `Vector2`
            The normalized vector.
        """

        try:
            return self.__class__(*super().normalize())
        except ValueError:
            return self.__class__()

    def direction_to(self, other: Self, /) -> Self:
        """
        Calculates the direction from this vector to another vector.

        Parameters
        ----------
        other: `Vector2`
            The other vector.

        Returns
        -------
        `Vector2`
            The direction from this vector to the other vector.
        """

        return (other - self).normalize()

    # probably premature optimization?
    # i mean, i'd look real stupid if this was slower just by virtue of being a python method as opposed to a c method
    def dirdist(self, other: Self, /) -> tuple[Self, float]:
        """
        Calculates both the direction from this vector to another vector, and the distance between them.\n
        Uses only one square root.

        Parameters
        ----------
        other: `Vector2`
            The other vector.

        Returns
        -------
        `tuple[Vector2, float]`
            The direction from this vector to the other vector, and the distance between them.
        """

        unnormalized_dir = other - self
        dist = unnormalized_dir.magnitude()
        return unnormalized_dir / dist, dist

    def clear(self) -> None:
        """Sets the x and y components of this vector to zero."""

        self.x = 0
        self.y = 0

    def with_x(self, x: float, /) -> Self:
        """Returns a new vector with the x-component set to `x`."""

        return self.__class__(x, self.y)

    def with_y(self, y: float, /) -> Self:
        """Returns a new vector with the y-component set to `y`."""

        return self.__class__(self.x, y)

    def with_inverted_x(self) -> Self:
        """Returns a new vector with the x-component inverted."""

        return self.__class__(-self.x, self.y)

    def with_inverted_y(self) -> Self:
        """Returns a new vector with the y-component inverted."""

        return self.__class__(self.x, -self.y)

    def to_int_tuple(self) -> tuple[int, int]:
        """
        This `Vector2` as a tuple of integers.\n
        Useful for passing the vector to pygame or other libraries' functions that tend expect a tuple of integers.

        Returns
        -------
        `tuple[int, int]`
            The vector as a tuple of integers.
        """

        return (int(self.x), int(self.y))


class Vector3(PygameVector3):
    """Replacement for `pygame.Vector3` with some extra utilities and exception-less versions of common methods"""

    @classmethod
    def zero(cls) -> Self:
        """Returns a zero `Vector3`. Same as `Vector3()`"""

        return cls(0, 0, 0)

    @classmethod
    def one(cls) -> Self:
        """Returns a `Vector3` with all components set to 1."""

        return cls(1, 1, 1)

    @classmethod
    def up(cls) -> Self:
        """Returns a `Vector3` pointing upwards."""

        return cls(0, 1, 0)

    @classmethod
    def down(cls) -> Self:
        """Returns a `Vector3` pointing downwards."""

        return cls(0, -1, 0)

    @classmethod
    def left(cls) -> Self:
        """Returns a `Vector3` pointing left."""

        return cls(-1, 0, 0)

    @classmethod
    def right(cls) -> Self:
        """Returns a `Vector3` pointing right."""

        return cls(1, 0, 0)

    @classmethod
    def forward(cls) -> Self:
        """Returns a `Vector3` pointing forward."""

        return cls(0, 0, 1)

    @classmethod
    def backward(cls) -> Self:
        """Returns a `Vector3` pointing backward."""

        return cls(0, 0, -1)

    @override
    def normalize(self) -> Self:
        """
        Normalizes the vector.\n
        Exception-less version of `pygame.Vector3.normalize`.

        Returns
        -------
        `Vector3`
            The normalized vector.
        """

        try:
            return self.__class__(*super().normalize())
        except ValueError:
            return self.__class__()

    def direction_to(self, other: Self, /) -> Self:
        """
        Calculates the direction from this vector to another vector.

        Parameters
        ----------
        other: `Vector3`
            The other vector.

        Returns
        -------
        `Vector3`
            The direction from this vector to the other vector.
        """

        return (other - self).normalize()

    # probably premature optimization?
    # i mean, i'd look real stupid if this was slower just by virtue of being a python method as opposed to a c method
    def dirdist(self, other: Self, /) -> tuple[Self, float]:
        """
        Calculates both the direction from this vector to another vector, and the distance between them.\n
        Uses only one square root.

        Parameters
        ----------
        other: `Vector3`
            The other vector.

        Returns
        -------
        `tuple[Vector3, float]`
            The direction from this vector to the other vector, and the distance between them.
        """

        unnormalized_dir = other - self
        dist = unnormalized_dir.magnitude()
        return unnormalized_dir / dist, dist

    def clear(self) -> None:
        """Sets the x, y and z components of this vector to zero."""

        self.x = 0
        self.y = 0
        self.z = 0

    def with_x(self, x: float, /) -> Self:
        """Returns a new `Vector3` with the x-component set to `x`."""

        return self.__class__(x, self.y, self.z)

    def with_y(self, y: float, /) -> Self:
        """Returns a new `Vector3` with the y-component set to `y`."""

        return self.__class__(self.x, y, self.z)

    def with_z(self, z: float, /) -> Self:
        """Returns a new `Vector3` with the z-component set to `z`."""

        return self.__class__(self.x, self.y, z)

    def with_inverted_x(self) -> Self:
        """Returns a new `Vector3` with the x-component inverted."""

        return self.__class__(-self.x, self.y, self.z)

    def with_inverted_y(self) -> Self:
        """Returns a new `Vector3` with the y-component inverted."""

        return self.__class__(self.x, -self.y, self.z)

    def with_inverted_z(self) -> Self:
        """Returns a new `Vector3` with the z-component inverted."""

        return self.__class__(self.x, self.y, -self.z)

    def to_int_tuple(self) -> tuple[int, int, int]:
        """
        This `Vector3` as a tuple of integers.\n
        Useful for passing the vector to pygame or other libraries' functions that tend expect a tuple of integers.

        Returns
        -------
        `tuple[int, int, int]`
            The vector as a tuple of integers.
        """

        return (int(self.x), int(self.y), int(self.z))


class Color(PygameColor):
    """Replacement for `pygame.Color` with some extra utilities and exception-less versions of common methods"""

    @classmethod
    def random(cls, minimum: int = 0, maximum: int = 255, /) -> Self:
        """
        Generates a random `Color` where each component is between `minimum` and `maximum`.

        Parameters
        ----------
        minimum: `int`
            The minimum value for each component. Defaults to 0.
        maximum: `int`
            The maximum value for each component. Defaults to 255.

        Returns
        -------
        `Color`
            A random color.
        """

        return cls(
            randint(minimum, maximum),
            randint(minimum, maximum),
            randint(minimum, maximum),
        )

    @override
    def lerp(
        self, color: PygameColor | SequenceLike[int] | str | int, amount: float
    ) -> PygameColor:
        """
        Interpolates between this color and another color.\n
        Exception-less version of `pygame.Color.lerp`.

        Parameters
        ----------
        color: `Color` | `SequenceLike[int]` | `str` | `int`
            The color to interpolate to.
        amount: `float`
            The amount to interpolate by. Clamped to between 0 and 1.

        Returns
        -------
        `Color`
            The interpolated color.
        """

        return super().lerp(color, clamp(amount, 0, 1))

    def brighten(self, amount: int, /) -> Self:
        """
        Brightens the color by the specified amount.

        Parameters
        ----------
        amount: `int`
            The amount to brighten the color by.

        Returns
        -------
        `Color`
            The brightened color.
        """

        return self.__class__(
            clamp(self.r + amount, 0, 255),  # pyright: ignore [reportArgumentType]
            clamp(self.g + amount, 0, 255),  # pyright: ignore [reportArgumentType]
            clamp(self.b + amount, 0, 255),  # pyright: ignore [reportArgumentType]
            self.a,
        )

    def darken(self, amount: int, /) -> Self:
        """
        Darkens the color by the specified amount.

        Parameters
        ----------
        amount: `int`
            The amount to darken the color by.

        Returns
        -------
        `Color`
            The darkened color.
        """

        return self.brighten(-amount)

    def invert(self) -> Self:
        """
        Inverts the color.

        Returns
        -------
        `Color`
            The inverted color.
        """

        return self.__class__(
            255 - self.r,
            255 - self.g,
            255 - self.b,
            self.a,
        )

    def with_r(self, r: int, /) -> Self:
        """
        Returns a new color with the specified red value.

        Parameters
        ----------
        r: `int`
            The red value.

        Returns
        -------
        `Color`
            The new color.
        """

        return self.__class__(
            r,
            self.g,
            self.b,
            self.a,
        )

    with_red = with_r  # alias

    def with_g(self, g: int, /) -> Self:
        """
        Returns a new color with the specified green value.

        Parameters
        ----------
        g: `int`
            The green value.

        Returns
        -------
        `Color`
            The new color.
        """

        return self.__class__(
            self.r,
            g,
            self.b,
            self.a,
        )

    with_green = with_g  # alias

    def with_b(self, b: int, /) -> Self:
        """
        Returns a new color with the specified blue value.

        Parameters
        ----------
        b: `int`
            The blue value.

        Returns
        -------
        `Color`
            The new color.
        """

        return self.__class__(
            self.r,
            self.g,
            b,
            self.a,
        )

    with_blue = with_b  # alias

    def with_a(self, a: int, /) -> Self:
        """
        Returns a new color with the specified alpha value.

        Parameters
        ----------
        a: `int`
            The alpha value.

        Returns
        -------
        `Color`
            The new color.
        """

        return self.__class__(
            self.r,
            self.g,
            self.b,
            a,
        )

    with_alpha = with_a  # alias

    def with_opacity(self, opacity: float, /) -> Self:
        """
        Returns a new color with the specified opacity (between 0 and 1).

        Parameters
        ----------
        opacity: `float`
            The opacity value.

        Returns
        -------
        `Color`
            The new color.

        Raises
        ------
        ValueError
            If the opacity is not between 0 and 1.
        """

        if not 0 <= opacity <= 1:
            raise ValueError("Opacity must be between 0 and 1")

        return self.__class__(
            self.r,
            self.g,
            self.b,
            int(opacity * 255),
        )


class Rect(PygameRect):
    """Replacement for `pygame.Rect` with some extra utilities."""

    @classmethod
    def from_center(cls, position: Vector2, size: Vector2, /) -> Self:
        """Returns a `Rect` with the given position and size, centered at the given position."""

        r = cls()
        r.size = size
        r.center = position

        return r


def get_by_attrs[T](iterable: Iterable[T], /, **attrs: Any) -> T | None:
    """
    Gets an element from an `Iterable` based on the specified attributes and values of those attributes.

    Examples
    --------
    >>> people = [
    ...     Person("Lucas", age=14),
    ...     Person("Marcus", age=51),
    ...     Person("Mary", age=23),
    ... ]
    >>> aged_twenty_three = get(people, age=23)
    Person('Mary', age=23)

    Parameters
    ----------
    iterable: `Iterable[T]`
        The iterable to get an element from.

    Returns
    -------
    `T | None`
        The element found. Or `None`, if no elements with matching attributes was found.
    """

    return first(filter_by_attrs(iterable, **attrs))


def filter_by_attrs[T](iterable: Iterable[T], /, **attrs: Any) -> Iterator[T]:
    """
    Filters an `Iterable` based on the specified attributes and values of those attributes.

    Parameters
    ----------
    iterable: `Iterable[T]`
        The `Iterable` to be filtered.

    Returns
    -------
    `Iterable[T]`
        The filtered `Iterable`.
    """

    return filter(
        lambda e: all(getattr(e, name) == value for name, value in attrs.items()),
        iterable,
    )


def first[T, TDefault](i: Iterable[T], /, *, default: TDefault = None) -> T | TDefault:
    """
    Consumes and gets the first element of an `Iterable`.

    Examples
    --------
    >>> first([1, 2, 3])
    1
    >>> first(range(10))
    0
    >>> first([])
    None
    >>> first([], default=True)
    True

    Parameters
    ----------
    i: `Iterable[T]`
        The `Iterable` to get the first element from.
    default: `TDefault`, optional
        The default value to return if the `Iterable` is empty.

    Returns
    -------
    `T | None`
        The first element of the `Iterable`, or `None` if the `Iterable` is empty.
    """

    try:
        return next(iter(i))
    except StopIteration:
        return default


def last[T, TDefault](i: Iterable[T], /, *, default: TDefault = None) -> T | TDefault:
    """
    Consumes and gets the last element of an `Iterable`.

    Examples
    --------
    >>> last([1, 2, 3])
    3
    >>> last(range(10))
    9
    >>> last([])
    None
    >>> last([], default=True)
    True

    Parameters
    ----------
    i: `Iterable[T]`
        The `Iterable` to get the last element from.
    default: `TDefault`, optional
        The default value to return if the `Iterable` is empty.

    Returns
    -------
    `T | None`
        The last element of the `Iterable`, or `None` if the `Iterable` is empty.
    """

    try:
        return next(reversed(tuple(i)))
    except StopIteration:
        return default


def ilen(i: Iterable[Any], /) -> int:
    """
    Consumes and returns the length of an `Iterable`.

    Parameters
    ----------
    i: `Iterable[Any]`
        The `Iterable` to get the length of.

    Returns
    -------
    `int`
        The length of the `Iterable`.
    """

    return sum(1 for _ in i)  # faster than len(tuple(i)) or len(list(i))


def mapl[T, U](f: Callable[[T], U], i: Iterable[T]) -> list[U]:
    """Like `map`, but it returns a `list` instead."""
    return list(map(f, i))


def filterl[T](f: Callable[[T], bool], i: Iterable[T]) -> list[T]:
    """Like `filter`, but it returns a `list` instead."""
    return list(filter(f, i))


def walk_neighbours[T](seq: Sequence[T], /) -> Iterable[tuple[T | None, T, T | None]]:
    """
    Walks a sequence, yielding each element along with its neighbours.\n
    For the first value, the left neighbour is `None` and for the last value, the right neighbour is `None`.
    Otherwise, all values are guaranteed to be of type T.

    Parameters
    ----------
    seq: `Sequence[T]`
        The sequence to walk.

    Yields
    ------
    `tuple[T | None, T, T | None]`
        The current element and its neighbours.
    """

    for i, el in enumerate(seq):
        yield (
            seq[i - 1] if i > 0 else None,
            el,
            seq[i + 1] if i < len(seq) - 1 else None,
        )


def animate(
    *,
    duration: float,
    step: Callable[[], float],
    easing: Callable[[float], float] = linear,
    force_end: bool = True,
) -> Generator[float]:
    """
    Generates a sequence of floats from 0 to 1, with a step size defined by `step`.
    Optionally, an easing function can be provided to control the values returned.
    Guaranteed to always yield 0, and, if `force_end` is `True`, 1.\n

    Examples
    --------
    ```python
    from sky import App, Coroutine
    from sky.colors import BLUE, RED
    from sky.utils import animate
    from sky.easing import bounce

    app = App()


    @app.setup
    def lerp_color() -> Coroutine:
        for t in animate(duration=3, step=lambda: app.chrono.deltatime, easing=bounce):
            app.window.surface.fill(RED.lerp(BLUE, t))
            yield None  # same as WaitForFrames(1)


    app.mainloop()
    ```

    Parameters
    ----------
    duration: `float`
        The duration of the animation.
    step: `Callable[[], float]`
        A function that returns the next step of the animation.\n
        For general real-time based animations, use `app.chrono.deltatime`.
    easing: `Callable[[float], float]`
        An easing function that controls the values returned.\n
        Defaults to `linear`. See the `easing` module for more options.
    force_end: `bool`
        Whether to force the function to yield 1 at the end of the animation.

    Yields
    ------
    `float`
        The next step of the animation, per the `step` function.

    Raises
    ------
    `ValueError`
        If `duration` is less than or equal to 0.
    """

    if duration <= 0:
        raise ValueError("`duration` must be greater than 0.")

    start = 0

    while start < duration:
        yield easing(start / duration)
        start = clamp(start + step(), 0, 1)

    if force_end:
        yield 1


def clamp(value: float, minimum: float, maximum: float, /) -> float:
    """
    Clamps a value between a minimum and maximum.

    Parameters
    ----------
    value: `float`
        The value to be clamped.
    minimum: `float`
        The minimum value.
    maximum: `float`
        The maximum value.

    Returns
    -------
    `float`
        The clamped value.\n
        Note: doesn't actually always return a `float`. For example, `clamp(1.5, 0, 1)` returns `maximum`, which is an `int` here, not a `float`.
        If you want it to always return a `float`, use upper and lower boundaries that are `floats`, or simply cast the result to a `float`.
    """

    return max(minimum, min(value, maximum))


constrain = clamp  # alias


def saturate(value: float, /) -> float:
    """
    Contains a value to between 0 and 1.

    Parameters
    ----------
    value: `float`
        The value to be saturated.

    Returns
    -------
    `float`
        The saturated value.
    """

    return clamp(value, 0, 1)


clamp01 = saturate  # alias


def singleton[C: type](cls: C, /) -> C:
    """Makes the decorated class a singleton while properly keeping its type."""

    return untyped_singleton(cls)  # pyright: ignore[reportReturnType]


def is_callable_with_no_arguments(callable: Callable[..., Any], /) -> bool:
    """
    Checks whether or not the given `Callable` can be called with no arguments.

    Parameters
    ----------
    callable: `Callable[..., Any]`
        The `Callable` to check.

    Returns
    -------
    `bool`
        Whether or not the `Callable` can be called with no arguments.
    """

    count = ilen(
        param
        for param in signature(callable).parameters.values()
        if param.default is Parameter.empty
    )
    return count == 0
