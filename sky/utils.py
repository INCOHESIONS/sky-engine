from random import randint
from typing import (
    Any,
    Callable,
    Generator,
    Iterable,
    Iterator,
    Self,
    overload,
    override,
)

from pygame import Color as PygameColor
from pygame import Vector2 as PygameVector2
from pygame.typing import SequenceLike

__all__ = [
    "animate",
    "Color",
    "filter_by_attrs",
    "first",
    "get_by_attrs",
    "last",
    "Vector2",
]


class Vector2(PygameVector2):
    """A 2D vector. Should be used instead of pygame.math.Vector2."""

    @override
    def normalize(self):
        """Exception-less version of `pygame.Vector2.normalize`."""

        try:
            return super().normalize()
        except ValueError:
            return Vector2()

    def direction_to(self, other: Self, /) -> Self:
        """
        Calculates the direction from this vector to another vector.

        Parameters
        ----------
        other : `Vector2`
            The other vector.

        Returns
        -------
        `Vector2`
            The direction from this vector to the other vector.
        """

        return (other - self).normalize()  # type: ignore

    # probably premature optimization?
    # i mean, i'd look real stupid if this was slower just by virtue of being a python method as opposed to a c method
    def dirdist(self, other: Self, /) -> tuple[Self, float]:
        """
        Calculates both the direction from this vector to another vector, and the distance between them.\n
        Uses only one square root.

        Parameters
        ----------
        other : `Vector2`
            The other vector.

        Returns
        -------
        `tuple[Vector2, float]`
            The direction from this vector to the other vector, and the distance between them.
        """

        unnormalized_dir = other - self
        dist = unnormalized_dir.magnitude()
        return unnormalized_dir / dist, dist

    def with_x(self, x: float) -> Self:
        """Returns a new vector with the x-component set to `x`."""

        return self.__class__(x, self.y)

    def with_y(self, y: float) -> Self:
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
        Gets the vector as a tuple of integers.\n
        Useful for passing the vector to pygame or other libraries' functions that tend expect a tuple of integers.

        Returns
        -------
        `tuple[int, int]`
            The vector as a tuple of integers.
        """

        return tuple(map(int, self))  # type: ignore


class Color(PygameColor):
    @classmethod
    def random(cls, minimum: int = 0, maximum: int = 255) -> Self:
        """
        Generates a random `Color` where each component is between `minimum` and `maximum`.

        Parameters
        ----------
        minimum : `int`
            The minimum value for each component.
        maximum : `int`
            The maximum value for each component.

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
        """Exception-less version of `pygame.Color.lerp`."""

        return super().lerp(color, clamp(amount, 0, 1))


def get_by_attrs[T](iterable: Iterable[T], /, **attrs: Any) -> T | None:
    """
    Gets an element from an `Iterable` based on the specified attributes and values of those attributes.

    Examples
    --------
    >>> people = [Person("Lucas", age=14), Person("Marcus", age=51), Person("Mary", age=23)]
    >>> aged_twenty_three = get(people, age=23)
    Person('Mary', age=23)

    Parameters
    ----------
    iterable : `Iterable[T]`
        The iterable to get an element from.

    Returns
    -------
    `T | None`
        The element found. Or `None`, if no elements with matching attributes was found.

    Raises
    ------
    `AttributeError`
        If an attribute wasn't found in an object of the iterable.
    """

    return first(filter_by_attrs(iterable, **attrs))


def filter_by_attrs[T](iterable: Iterable[T], /, **attrs: Any) -> Iterator[T]:
    """
    Filters an `Iterable` based on the specified attributes and values of those attributes.

    Parameters
    ----------
    iterable : `Iterable[T]`
        The `Iterable` to be filtered.

    Returns
    -------
    `Iterable[T]`
        The filtered `Iterable`.

    Raises
    ------
    `AttributeError`
        If an attribute wasn't found in an object of the iterable.
    """

    return filter(
        lambda e: all(getattr(e, name) == value for name, value in attrs.items()),
        iterable,
    )


@overload
def first[T, TDefault](i: Iterable[T], /, *, default: TDefault) -> T | TDefault: ...


@overload
def first[T, TDefault](
    i: Iterable[T], /, *, default: TDefault = None
) -> T | TDefault: ...


def first[T, TDefault](i: Iterable[T], /, *, default: TDefault = None) -> T | TDefault:
    """
    Gets the first element of an `Iterable`.

    Examples
    --------
    >>> first([1, 2, 3])
    1
    >>> first(range(10))
    0
    >>> first([])
    None

    Parameters
    ----------
    i : `Iterable[T]`
        The `Iterable` to get the first element from.

    Returns
    -------
    `T | None`
        The first element of the `Iterable`, or `None` if the `Iterable` is empty.
    """

    try:
        return next(iter(i))
    except StopIteration:
        return default


@overload
def last[T, TDefault](i: Iterable[T], /, *, default: TDefault) -> T | TDefault: ...


@overload
def last[T, TDefault](
    i: Iterable[T], /, *, default: TDefault = None
) -> T | TDefault: ...


def last[T, TDefault](i: Iterable[T], /, *, default: TDefault = None) -> T | TDefault:
    """
    Gets the last element of an `Iterable`.

    Examples
    --------
    >>> last([1, 2, 3])
    3
    >>> last(range(10))
    9
    >>> last([])
    None

    Parameters
    ----------
    i : `Iterable[T]`
        The `Iterable` to get the last element from.

    Returns
    -------
    `T | None`
        The last element of the `Iterable`, or `None` if the `Iterable` is empty.
    """

    try:
        return next(reversed(tuple(i)))
    except StopIteration:
        return default


def animate(
    *, duration: float, step: Callable[[], float], normalize: bool = True
) -> Generator[float]:
    """
    Generates a sequence of floats from 0 to `duration`, with a step size defined by `step`.\n
    If normalize is `True`, the sequence will be normalized to the range [0, 1].
    Useful for interpolating between two colors over time, for example.

    Guaranteed to always yield both 0 and `duration`. Might yield `duration` (or 1 if `normalize` is `True`) twice.

    Examples
    --------
    ```python
    from sky import App
    from sky.colors import BLUE, RED
    from sky.types import Coroutine
    from sky.utils import animate

    app = App()


    @app.setup
    def lerp_color() -> Coroutine:
        assert app.windowing.surface is not None

        for t in animate(duration=3, step=lambda: app.chrono.deltatime):
            app.windowing.surface.fill(RED.lerp(BLUE, t))
            yield None  # same as WaitForFrames(1)


    app.mainloop()
    ```

    Parameters
    ----------
    duration : `float`
        The duration of the animation.
    step : `Callable[[], float]`
        A function that returns the next step of the animation.\n
        For general real-time based animations, use `app.chrono.deltatime`.
    normalize : `bool`
        Whether to normalize the animation to the range [0, 1].\n

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
        if normalize:
            yield start / duration
        else:
            yield start

        start = clamp(start + step(), 0, duration)

    # this is done to guarantee `duration` or 1 will always be yielded, but may cause it to be yielded twice, or almost
    # example: step = lambda: 0.49; the function will yield 0, step, 0.98 and 1 again
    # if we didn't do this, `duration` might not be yielded, and could cause strange behaviour while interpolating values since the stop value would never be used
    # this is a fine trade-off

    yield 1 if normalize else duration


def clamp(value: float, minimum: float, maximum: float, /) -> float:
    """
    Clamps a value between a minimum and maximum.

    Parameters
    ----------
    value : `float`
        The value to be clamped.
    minimum : `float`
        The minimum value.
    maximum : `float`
        The maximum value.

    Returns
    -------
    `float`
        The clamped value.\n
        Note: doesn't actually always return a `float`. For example, `clamp(1.5, 0, 1)` returns `maximum`, which is an `int` here, not a `float`.
        If you want it to always return a `float`, use upper and lower boundaries that are `floats`, or simply cast the result to a `float`.
    """

    return max(minimum, min(value, maximum))


constrain = clamp
