import os

from .utils import Color, Vector2

__all__ = [
    "get_mouse_position",
    "get_window_handle",
    "hide_window",
    "transparentize_window",
]


if os.name == "nt":
    import win32api
    import win32con
    import win32gui

    def transparentize_window(hwnd: int, colorkey: Color, /) -> None:
        win32gui.SetWindowLong(  # pyright: ignore[reportUnknownMemberType]
            hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            | win32con.WS_EX_LAYERED,
        )

        win32gui.SetLayeredWindowAttributes(  # pyright: ignore[reportUnknownMemberType]
            hwnd,
            win32api.RGB(*colorkey.rgb),
            0,
            win32con.LWA_COLORKEY,
        )

    def hide_window(hwnd: int, /) -> None:
        win32gui.SetWindowLong(  # pyright: ignore[reportUnknownMemberType]
            hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
            & ~win32con.WS_EX_APPWINDOW
            | win32con.WS_EX_TOOLWINDOW,
        )

        win32gui.SetWindowPos(
            hwnd,
            None,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE
            | win32con.SWP_NOSIZE
            | win32con.SWP_NOZORDER
            | win32con.SWP_FRAMECHANGED,
        )

    def get_window_handle(title: str, /) -> int:
        return win32gui.FindWindow(None, title)

    def get_mouse_position() -> Vector2:
        return Vector2(win32api.GetCursorPos())


else:

    def transparentize_window(_1: int, _2: Color, /) -> None:
        raise OSError("This method is only supported on Windows.")

    def hide_window(_: int, /) -> None:
        raise OSError("This method is only supported on Windows.")

    def get_window_handle(_: str, /) -> int:
        raise OSError("This method is only supported on Windows.")

    def get_mouse_position() -> Vector2:
        raise OSError("This method is only supported on Windows.")
