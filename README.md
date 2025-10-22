# Sky Engine

Makes `pygame` ([pygame-ce](https://github.com/pygame-community/pygame-ce), more specifically) less painful to use. More like a wrapper than an engine. Fully typed with [basedpyright](https://github.com/DetachHead/basedpyright).

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


@app.component
@dataclass
class Player(Component):
    position: Vector2 = field(default_factory=app.window.center.copy)

    @override
    def update(self):
        self.position += app.keyboard.get_movement_2d(("a", "d"), ("w", "s"))
        pygame.draw.circle(app.window.surface, WHITE, self.position, 25)


app.mainloop()
```

Although that example uses `pygame.draw`, one may use any other library that supports Vulkan or OpenGL. See [this](https://github.com/incohesions/sky-engine/tree/main/examples/hello_triangle.py) for an example using `zengl`.

For examples on other Sky Engine features, see the [examples](https://github.com/incohesions/sky-engine/tree/main/examples) folder.
