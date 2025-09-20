from dataclasses import dataclass, field
from random import randint

import pygame

from sky import App, Color, Key, MouseButton, Vector2

app = App()
app.keyboard.add_keybindings({
    Key.escape: app.quit,
    Key.f11: app.windowing.toggle_fullscreen,
})  # fmt: skip


@dataclass
class Circle:
    position: Vector2
    velocity: Vector2
    acceleration: Vector2 = field(default_factory=Vector2)
    radius: float = field(default_factory=lambda: randint(10, 20))
    color: Color = field(default_factory=Color.random)

    def update(self) -> None:
        if app.mouse.is_pressed(MouseButton.right):
            self.acceleration += self.position.direction_to(app.mouse.position)

        if app.mouse.is_pressed(MouseButton.middle):
            self.acceleration -= self.position.direction_to(app.mouse.position) * 3

        self.velocity *= 0.999
        self.velocity += self.acceleration
        self.position += self.velocity
        self.acceleration = Vector2()

    def render(self) -> None:
        pygame.draw.circle(
            app.windowing.surface,  # type: ignore
            self.color,
            self.position,
            self.radius * 2,
        )


circles: list[Circle] = []


@app.pre_update
def pre_update() -> None:
    app.windowing.surface.fill("#141417")  # type: ignore

    for circle in circles:
        circle.update()
        circle.render()


@app.mouse.on_mouse_button_downed.equals(MouseButton.left)
def on_mouse_button_downed() -> None:
    circles.append(Circle(app.mouse.position, Vector2(), app.mouse.velocity / 3))


app.mainloop()
