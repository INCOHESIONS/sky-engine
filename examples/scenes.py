from dataclasses import dataclass, field
from random import randint
from typing import override

from pygame.gfxdraw import aacircle as draw_outline
from pygame.gfxdraw import filled_circle as draw_circle

from sky import App, AppSpec, Color, Component, Key, Scene, Vector2, WindowSpec
from sky.colors import BLUE, RED

app = App(
    spec=AppSpec(window_spec=WindowSpec(fill=Color("#0D1016")), default_scene=False)
)
app.keyboard.add_keybindings({Key.escape: app.quit})


@dataclass
class Circle:
    color: Color

    position: Vector2 = field(
        default_factory=lambda: app.window.center + Vector2.random() * 100
    )
    velocity: Vector2 = field(default_factory=Vector2.random)
    acceleration: Vector2 = field(default_factory=Vector2)
    radius: int = field(default_factory=lambda: randint(10, 20))

    def update(self) -> None:
        self.velocity *= 0.999
        self.velocity += self.acceleration
        self.position += self.velocity
        self.acceleration = Vector2()

    def render(self) -> None:
        draw_circle(
            app.window.surface,
            *self.position.to_int_tuple(),
            self.radius,
            self.color,
        )

        draw_outline(
            app.window.surface,
            *self.position.to_int_tuple(),
            self.radius + 1,
            self.color.invert(),
        )


class Circles(Component):
    def __init__(self, color: Color, /) -> None:
        self._circles = [Circle(color) for _ in range(10)]

    @override
    def update(self) -> None:
        for circle in self._circles:
            circle.update()
            circle.render()


app.load_scene(red := Scene([Circles(RED)]))
app.load_scene(Scene([Circles(BLUE)]))


@app.keyboard.on_key_downed.equals(Key.space)
def on_space() -> None:
    app.toggle_scene(red)


app.mainloop()
