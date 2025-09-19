from typing import Any, Iterable, Iterator, overload

from pygame import Vector2 as PygameVector2

__all__ = ["filter_by_attrs", "first", "get_by_attrs", "last", "Vector2"]


class Vector2(PygameVector2):
    def to_int_tuple(self) -> tuple[int, int]:
        return tuple(map(int, self))  # type: ignore


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
