from dataclasses import dataclass
from typing import override

from pygame import draw

from sky import App, AppSpec, Color, Component, Scene, Vector2
from sky.colors import BLUE, RED

app = App(spec=AppSpec.sceneless())  # no default scene since we'll add our own


@dataclass
class Circle(Component):
    pos: Vector2
    color: Color

    @override
    def update(self):
        draw.aacircle(app.window.surface, self.color, self.pos, 50)


app.load_scene(
    red_scene := Scene.from_components(
        [Circle(app.window.center + Vector2(100, 0), BLUE)]
    )
)
app.load_scene(
    blue_scene := Scene.from_components(
        [Circle(app.window.center - Vector2(100, 0), RED)]
    )
)

app.keyboard.add_keybindings(
    a=lambda: app.toggle_scene(blue_scene), b=lambda: app.toggle_scene(red_scene)
)

app.mainloop()
