from typing import Callable

from pygame import freetype

from sky import App, Window, WindowSpec
from sky.colors import WHITE

app = App(spec=WindowSpec(title="Main Window!"), modules=[freetype])

font = freetype.SysFont("Arial", 32)


def render(window: Window) -> Callable[[], None]:
    def wrapped() -> None:
        font.render_to(window.surface, window.center, window.title, WHITE)

    return wrapped


main_window = app.window
secondary_window = app.windowing.add_window(spec=WindowSpec(title="Extra Window!"))

main_window.on_render += render(main_window)
secondary_window.on_render += render(secondary_window)

app.mainloop()
