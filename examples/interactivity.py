from dataclasses import dataclass, field
from random import randint
from typing import override

import pygame

from sky import App, Color, Component, Key, MouseButton, Vector2, WindowSpec

app = App(spec=WindowSpec(fill=Color("#141417")))
app.keyboard.add_keybindings({
    Key.escape: app.quit,
    Key.f11: app.window.toggle_fullscreen,
})  # fmt: skip


@dataclass
class Circle(Component):
    position: Vector2
    velocity: Vector2
    acceleration: Vector2
    radius: float = field(default_factory=lambda: randint(10, 20))
    color: Color = field(default_factory=Color.random)

    @override
    def update(self) -> None:
        if app.mouse.is_pressed(MouseButton.right):
            self.acceleration += self.position.direction_to(app.mouse.position)

        if app.mouse.is_pressed(MouseButton.middle):
            self.acceleration -= self.position.direction_to(app.mouse.position) * 3

        self.velocity *= 0.999
        self.velocity += self.acceleration
        self.position += self.velocity
        self.acceleration = Vector2()

        self.render()

    def render(self) -> None:
        pygame.draw.circle(
            app.window.surface,
            self.color,
            self.position,
            self.radius * 2,
        )


@app.mouse.on_mouse_button_downed.equals(MouseButton.left)
def on_mouse_button_downed() -> None:
    app.add_component(Circle(app.mouse.position, Vector2(), app.mouse.velocity / 3))


app.mainloop()
