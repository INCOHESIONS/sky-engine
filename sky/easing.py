"""Easing functions, provided by https://easings.net. See also: `sky.utils.animate`."""

import math
from typing import Callable, LiteralString

from .utils import Vector2

__all__ = [
    "bounce_in",
    "bounce_in_out",
    "bounce_out",
    "cubic",
    "cubic_in",
    "cubic_in_out",
    "cubic_out",
    "elastic_in",
    "elastic_in_out",
    "elastic_out",
    "expo",
    "expo_in",
    "expo_in_out",
    "expo_out",
    "linear",
    "quad",
    "quad_in",
    "quad_in_out",
    "quad_out",
    "quint",
    "quint_in",
    "quint_in_out",
    "quint_out",
]


def linear(t: float, /) -> float:
    return t


def cubic_in(t: float, /) -> float:
    return 1.0 - math.pow(1.0 - t, 3.0)


def cubic_out(t: float, /) -> float:
    return t * t * t


def cubic_in_out(t: float, /) -> float:
    return 4.0 * t * t * t if t < 0.5 else 1.0 - math.pow(-2.0 * t + 2.0, 3.0) / 2.0


cubic = cubic_in_out  # alias


def quad_in(t: float, /) -> float:
    return t * t


def quad_out(t: float, /) -> float:
    return 1.0 - (1.0 - t) * (1.0 - t)


def quad_in_out(t: float, /) -> float:
    return 2.0 * t * t if t < 0.5 else 1.0 - math.pow(-2.0 * t + 2.0, 2.0) / 2.0


quad = quad_in_out  # alias


def quint_in(t: float, /) -> float:
    return t * t * t * t * t


def quint_out(t: float, /) -> float:
    return 1.0 - math.pow(1.0 - t, 5.0)


def quint_in_out(t: float, /) -> float:
    return (
        16.0 * t * t * t * t * t
        if t < 0.5
        else 1.0 - math.pow(-2.0 * t + 2.0, 5.0) / 2.0
    )


quint = quint_in_out  # alias


def expo_in(t: float, /) -> float:
    return 0.0 if t == 0.0 else math.pow(2.0, 10.0 * t - 10.0)


def expo_out(t: float, /) -> float:
    return 1.0 if t == 1.0 else 1.0 - math.pow(2.0, -10.0 * t)


def expo_in_out(t: float, /) -> float:
    if t == 0.0 or t == 1.0:
        return t

    return (
        math.pow(2.0, 20.0 * t - 10.0) / 2.0
        if t < 0.5
        else (2.0 - math.pow(2.0, -20.0 * t + 10.0)) / 2.0
    )


expo = expo_in_out  # alias


def bounce_in(t: float, /) -> float:
    return 1.0 - bounce_out(1.0 - t)


def bounce_out(t: float, /) -> float:
    n1 = 7.5625
    d1 = 2.75

    if t < 1.0 / d1:
        return n1 * t * t
    elif t < 2.0 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def bounce_in_out(t: float, /) -> float:
    return (
        (1.0 - bounce_out(1.0 - 2.0 * t)) / 2.0
        if t < 0.5
        else (1.0 + bounce_out(2.0 * t - 1.0)) / 2.0
    )


bounce = bounce_in_out


def elastic_in(t: float, /) -> float:
    if t == 0.0 or t == 1.0:
        return t

    c4 = (2.0 * math.pi) / 3.0

    return -math.pow(2.0, 10.0 * t - 10.0) * math.sin((t * 10.0 - 10.75) * c4)


def elastic_out(t: float, /) -> float:
    if t == 0.0 or t == 1.0:
        return t

    c4 = 2.0 * math.pi / 3.0

    return math.pow(2.0, -10.0 * t) * math.sin((t * 10.0 - 0.75) * c4) + 1.0


def elastic_in_out(t: float, /) -> float:
    c5 = (2.0 * math.pi) / 4.5

    if t == 0.0 or t == 1.0:
        return t

    if t < 0.5:
        return (
            -(math.pow(2.0, 20.0 * t - 10.0) * math.sin((20.0 * t - 11.125) * c5)) / 2.0
        )

    return (
        math.pow(2.0, -20.0 * t + 10.0) * math.sin((20.0 * t - 11.125) * c5)
    ) / 2.0 + 1.0


def cubic_bezier(
    name: LiteralString, x1: float, y1: float, x2: float, y2: float, /
) -> Callable[[float], float]:
    p0 = Vector2.zero()
    p1 = Vector2(x1, y1)
    p2 = Vector2(x2, y2)
    p3 = Vector2.one()

    def _calculate(t: float, /):
        return (
            (1 - t) ** 3 * p0
            + 3 * (1 - t) ** 2 * t * p1
            + 3 * (1 - t) * t**2 * p2
            + t**3 * p3
        ).y

    _calculate.__name__ = name

    return _calculate


ease = cubic_bezier("ease", 0.25, 0.1, 0.25, 1)
ease_in = cubic_bezier("ease_in", 0.42, 0, 1, 1)
ease_out = cubic_bezier("ease_out", 0, 0, 0.58, 1)
ease_in_out = cubic_bezier("ease_in_out", 0.42, 0, 0.58, 1)
