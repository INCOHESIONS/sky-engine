from dataclasses import dataclass, field
from random import randint
from typing import ClassVar, override

from pygame.gfxdraw import aacircle as draw_outline
from pygame.gfxdraw import filled_circle as draw_circle

from sky import App, AppSpec, Color, Component, Key, Scene, Vector2, WindowSpec
from sky.colors import BLUE, RED, WHITE

app = App(
    spec=AppSpec(window_spec=WindowSpec(fill=Color("#0D1016")), scene_spec=None),
)


@dataclass
class Circle:
    color: Color

    position: Vector2 = field(
        default_factory=lambda: app.window.center + Vector2.random() * 100
    )
    velocity: Vector2 = field(default_factory=Vector2.random)
    acceleration: Vector2 = field(default_factory=Vector2)
    radius: int = field(default_factory=lambda: randint(10, 20))

    friction: ClassVar[float] = 0.999

    def update(self) -> None:
        self.velocity += (
            self.position.direction_to(app.window.center) * app.chrono.deltatime
        )

        self.velocity *= self.friction
        self.velocity += self.acceleration
        self.position += self.velocity

        self.acceleration.clear()

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
            WHITE,
        )


class Circles(Component):
    def __init__(self, color: Color, /) -> None:
        self._circles = [Circle(color) for _ in range(10)]

    @override
    def update(self) -> None:
        for circle in self._circles:
            circle.update()
            circle.render()


app.load_scene(red := Scene.from_components([Circles(RED)]))
app.load_scene(blue := Scene.from_components([Circles(BLUE)]))

app.keyboard.add_keybindings({
    Key.a: lambda: app.toggle_scene(red),
    Key.b: lambda: app.toggle_scene(blue),
    Key.escape: app.quit,
})  # fmt: skip

app.mainloop()
