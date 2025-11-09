"""
Unique sentinel values. Based on PEP 661.
See: https://peps.python.org/pep-0661/#reference-implementation
"""

from __future__ import annotations

import inspect
from typing import LiteralString, Self, final, override

_sentinels: dict[str, Sentinel] = {}


def get_prev_module_name() -> str:
    try:
        return inspect.getmodule(inspect.currentframe().f_back.f_back).__name__  # pyright: ignore[reportOptionalMemberAccess]
    except AttributeError:
        return __name__


@final
class Sentinel:
    """Class for creating unique sentinel values."""

    _id: str  # pyright: ignore[reportUninitializedInstanceVariable]

    @override
    def __new__(
        cls, name: LiteralString, /, *, module_name: str | None = None
    ) -> Sentinel:
        id = f"{module_name or get_prev_module_name()}-{name}"

        if (existing := _sentinels.get(id, None)) is not None:
            return existing

        sentinel = super().__new__(cls)
        sentinel._id = id

        return _sentinels.setdefault(id, sentinel)

    @override
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.name}", module_name="{self.module_name}")'

    @override
    def __reduce__(self) -> tuple[type[Self], tuple[str, str]]:
        return (
            self.__class__,
            (
                self.name,
                self.module_name,
            ),
        )

    @property
    def name(self) -> str:
        """This `Sentinel`'s name."""

        return self._id.split("-")[-1]

    @property
    def module_name(self) -> str:
        """This `Sentinel`'s module's name."""

        return self._id.split("-")[0]
