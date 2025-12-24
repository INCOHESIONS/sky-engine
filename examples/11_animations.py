from dataclasses import dataclass
from typing import Callable, override

from pygame import draw as render
from pygame import freetype

from sky import (
    App,
    AppSpec,
    Color,
    Component,
    Coroutine,
    Vector2,
    WaitForSeconds,
    WaitUntil,
    WindowSpec,
)
from sky.colors import CRIMSON, WHITE
from sky.easing import bounce_out, cubic_in_out, ease_in_out, linear, quint_in_out
from sky.utils import animate

app = App(
    spec=AppSpec(
        window_spec=WindowSpec(fill=Color("#111113")),
        modules=[freetype],
    )
)

font = freetype.SysFont("Arial", 24)


@dataclass
class Circle(Component):
    easing: Callable[[float], float]
    position: Vector2

    def __post_init__(self) -> None:
        self._start = self.position.copy()

    @override
    def start(self) -> Coroutine:
        yield WaitUntil(lambda: app.is_running)
        app.executor.start_coroutine(self.animate)

    @override
    def update(self) -> None:
        render.aacircle(app.window.surface, CRIMSON, self.position, 32)

        surface, rect = font.render(
            self.easing.__name__, WHITE, style=freetype.STYLE_STRONG
        )
        rect.center = self.position
        app.window.blit(surface, rect)

    def animate(self) -> Coroutine:
        while app.is_running:
            start = self._start
            end = start.with_x(app.window.width - start.x)

            for t in animate(
                duration=2, easing=self.easing, step=lambda: app.chrono.deltatime
            ):
                self.position = start.lerp(end, t)
                yield None

            yield WaitForSeconds(1)


for i, easing in enumerate(
    (linear, cubic_in_out, quint_in_out, ease_in_out, bounce_out)
):
    app.add_component(Circle(easing, Vector2(100, 60 + 120 * i)))

app.mainloop()
