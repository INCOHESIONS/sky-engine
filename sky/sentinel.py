"""Sentinel values based on PEP 661."""

from __future__ import annotations

import sys
from typing import LiteralString, final, override

__all__ = ["Sentinel"]

_sentinels: dict[str, Sentinel] = {}


@final
class Sentinel:
    """
    Unique sentinel values.
    See: https://peps.python.org/pep-0661/#reference-implementation
    """

    _name: str  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls, name: LiteralString, /) -> Sentinel:
        if (cached := _sentinels.get(name, None)) is not None:
            return cached

        module = sys._getframemodulename(1) or __name__  # pyright: ignore[reportPrivateUsage]
        qualified_name = f"{module}.{name}"

        sentinel = super().__new__(cls)
        sentinel._name = qualified_name

        return _sentinels.setdefault(name, sentinel)

    @override
    def __repr__(self) -> str:
        return self._name
