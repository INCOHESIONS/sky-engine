from pygame import draw

from sky import App, AppSpec, Color, Window, WindowSpec
from sky.colors import CRIMSON, DODGER_BLUE
from sky.utils import discard

app = App(spec=AppSpec.headless())

window1 = app.windowing.add_window(spec=WindowSpec(title="Window 1", fill=CRIMSON))
window2 = app.windowing.add_window(spec=WindowSpec(title="Window 2", fill=DODGER_BLUE))


def render_to(window: Window, color: Color) -> None:
    window.on_render += lambda: discard(
        draw.aacircle(window.surface, color, window.center, 32)
    )


render_to(window1, DODGER_BLUE)
render_to(window2, CRIMSON)


app.mainloop()
