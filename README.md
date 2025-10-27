# Sky Engine

Makes `pygame` (or rather, [pygame-ce](https://github.com/pygame-community/pygame-ce), more specifically) less painful to use. More like a wrapper than an engine. Fully typed with [basedpyright](https://github.com/DetachHead/basedpyright).

Theoretically cross-platform, but mostly tested on Windows. May have some window manager weirdness on Linux, specifically when it comes to fullscreening.

## Quick Start

Only 2 lines of code are needed to get started. This opens a window, centered on the screen, with a black background:

```python
from sky import App

App().mainloop()
```

To modify the window's properties, use the `spec` argument:
```python
from sky import App, WindowSpec

App(spec=WindowSpec(title="My Window!", state="fullscreened")).mainloop()
```

The building blocks of Sky Engine are `Component`s. For example, this is how one might create a simple `Player` component that renders a circle at a position:

```python
from dataclasses import dataclass, field
from typing import override

import pygame

from sky import App, Component, Vector2
from sky.colors import WHITE

app = App()


@dataclass
class Player(Component):
    position: Vector2 = field(default_factory=app.window.center.copy)

    @override
    def update(self):
        self.position += app.keyboard.get_movement_2d(("a", "d"), ("w", "s"))
        pygame.draw.circle(app.window.surface, WHITE, self.position, 25)


app.add_component(Player)
app.mainloop()
```

`Component`s are contained within `Scene`s. The example above uses `add_component` directly on `App`, which adds a component to the default scene, created via a `SceneSpec` argument in `AppSpec`.

Here's a simple showcase of `Scene`s:

```python
from typing import override

import pygame

from sky import App, AppSpec, Color, Key, Scene, SceneSpec, Vector2
from sky.colors import BLUE, RED

app = App(spec=AppSpec.sceneless())  # no default scene since we'll add our own


class CircleScene(Scene):
    def __init__(self, pos: Vector2, color: Color, /):
        super().__init__(spec=SceneSpec())

        self.pos = pos
        self.color = color

    @override
    def update(self):
        pygame.draw.circle(app.window.surface, self.color, self.pos, 50)


app.load_scene(red_scene := CircleScene(app.window.center + Vector2(100, 0), RED))
app.load_scene(blue_scene := CircleScene(app.window.center - Vector2(100, 0), BLUE))

app.keyboard.add_keybindings({
    Key.a: lambda: app.toggle_scene(red_scene),
    Key.b: lambda: app.toggle_scene(blue_scene),
    Key.escape: app.quit,
})

app.mainloop()
```

Although both of these examples use software rendering with `pygame.draw`, one may alternatively use Vulkan or OpenGL libraries for hardware rendering. See [this](https://github.com/incohesions/sky-engine/tree/main/examples/hello_triangle.py) for an example using `zengl`.

For examples on other Sky Engine features, see the [examples](https://github.com/incohesions/sky-engine/tree/main/examples) folder.
