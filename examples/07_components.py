from dataclasses import dataclass, field
from typing import override

from pygame import draw

from sky import App, Component, Vector2, WindowSpec
from sky.colors import ALICE_BLUE, CRIMSON

app = App(spec=WindowSpec(fill=CRIMSON))


@dataclass
class Player(Component):
    pos: Vector2 = field(default_factory=lambda: app.window.center)
    speed: float = 2
    radius: int = 32

    @override
    def update(self) -> None:
        self.pos += app.keyboard.get_movement_2d(("a", "d"), ("w", "s")) * self.speed

        if app.mouse.any("downed"):
            self.radius += -1 if app.mouse.is_downed("right") else 1

        draw.aacircle(app.window.surface, ALICE_BLUE, self.pos, self.radius)


app.add_component(Player)
app.mainloop()
