from dataclasses import dataclass, field
from typing import override

from pygame import draw

from sky import App, Component, MouseButton, Vector2, WindowSpec
from sky.colors import ALICE_BLUE, CRIMSON

app = App(spec=WindowSpec(fill=CRIMSON))
app.keyboard.add_keybindings(escape=app.quit)


@dataclass
class Player(Component):
    pos: Vector2 = field(default_factory=lambda: app.window.center)
    speed: float = 2
    radius: int = 32

    @override
    def start(self) -> None:
        app.mouse.on_mouse_button_downed += self.change_radius

    @override
    def update(self) -> None:
        self.pos += app.keyboard.get_movement_2d(("a", "d"), ("w", "s")) * self.speed
        draw.aacircle(app.window.surface, ALICE_BLUE, self.pos, self.radius)

    def change_radius(self, button: MouseButton) -> None:
        self.radius += -1 if button == MouseButton.right else 1


app.add_component(Player)
app.mainloop()
