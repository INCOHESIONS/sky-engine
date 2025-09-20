from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from .core import Yieldable
    from .enums import Cursor, Key, MouseButton


type KeyLike = Key | str | int
type MouseButtonLike = MouseButton | str | int
type CursorLike = Cursor | str | int

type Coroutine = Generator[type[Yieldable] | Yieldable | None, None, None]
