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

        if amount < 0:
            return self
        if amount > 1:
            return Color(color)
        return super().lerp(color, amount)


def get_by_attrs[T](iterable: Iterable[T], /, **attrs: Any) -> T | None:
    """
    Gets an element from an `Iterable` based on the specified attributes and values of those attributes.

    Examples
    --------
    >>> people = [Person('Lucas', age=14), Person('Marcus', age=51), Person('Mary', age=23)]
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

    return next(filter_by_attrs(iterable, **attrs), None)


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
def first[T](i: Iterable[T], /, *, default: T) -> T | None: ...


@overload
def first[T](i: Iterable[T], /, *, default: T | None = None) -> T | None: ...


def first[T](i: Iterable[T], /, *, default: T | None = None) -> T | None:
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
def last[T](i: Iterable[T], /, *, default: T) -> T: ...


@overload
def last[T](i: Iterable[T], /, *, default: T | None = None) -> T | None: ...


def last[T](i: Iterable[T], /, *, default: T | None = None) -> T | None:
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
    """

    try:
        return next(reversed(tuple(i)))
    except StopIteration:
        return default


def animate(*, duration: float, step: Callable[[], float]) -> Generator[float]:
    """
    Generates a sequence of floats from 0 to 1, with a step size of 1/duration.\n
    Useful for interpolating between two colors over time, for example.

    Parameters
    ----------
    duration : `float`
        The duration of the animation.
    step : `Callable[[], float]`
        A function that returns the next step of the animation.\n
        For general real-time based animations, use `app.chrono.deltatime`.

    Yields
    ------
    `float`
        The next step of the animation, per the `step` function.
    """

    start = 0

    while start < duration:
        yield start / duration
        start += step()
