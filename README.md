# Sky Engine

Makes `pygame` (or rather, [pygame-ce](https://github.com/pygame-community/pygame-ce), more specifically) less painful to use. More like a wrapper than an engine. Fully typed with [basedpyright](https://github.com/DetachHead/basedpyright).

Theoretically cross-platform, but mostly tested on Windows. May have some window manager weirdness on Linux, specifically when it comes to fullscreening.

## Quick Start

Due to the engine's many defaults, only 2 lines of code are needed to get started. This opens an 800x600 window, centered on the main monitor, with a black background:

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

`Component`s are contained within `Scene`s. The example above uses `add_component` directly on `App`, which adds a component to the current scene, which, in this case, is the default scene, created via a `SceneSpec` argument in `AppSpec`.

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

So far we've used `pygame.draw` for rendering, but the engine doesn't rely on it, and can perform any other form of rendering using any library. For instance, here's a more complicated program: interactive [Worley Noise](https://en.wikipedia.org/wiki/Worley_noise) generation, using [compushady](https://github.com/rdeioris/compushady/) and [HLSL](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-reference) for hardware rendering:
```python
# pyright: reportMissingTypeStubs=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
# ^ compushady lacks stubs so this is to prevent a bunch of type checking errors from flashing you

import struct
from ctypes import c_int, sizeof
from functools import cached_property
from itertools import chain as flatten
from random import uniform
from typing import final, override

import compushady
from compushady.formats import B8G8R8A8_UNORM, R32G32_UINT
from compushady.shaders.hlsl import compile

from sky import App, Component, Key, Vector2

compushady.config.set_debug(True)

app = App()
app.keyboard.add_keybinding((Key.escape, app.quit))


@final
@app.singleton_component
class Renderer(Component):
    COUNT = 16

    SHADER = f"""
        #define INFINITY 3.402823466e+38F

        RWTexture2D<float4> target;
        Buffer<int2> points;

        [numthreads(8, 8, 1)]
        void main(uint3 tid : SV_DispatchThreadID)
        {{
            float minDist = INFINITY;

            for (int i = 0; i < {COUNT}; i++)
                minDist = min(minDist, distance(points[i], tid.xy));

            const float color = 1.0F - saturate(minDist / 128.0F);

            target[tid.xy] = float4(color, color, color, 1.0F);
        }}
    """

    def __init__(self):
        self.target = compushady.Texture2D(*app.window.isize, format=B8G8R8A8_UNORM)
        self.swapchain = compushady.Swapchain(app.window.handle, format=B8G8R8A8_UNORM)

        self.generate_points()

        self.compute = compushady.Compute(
            compile(self.SHADER), uav=[self.target], srv=[self.points_buffer]
        )

        app.keyboard.add_keybinding((Key.space, self.generate_points))

    @override
    def stop(self) -> None:
        self.swapchain = None

    @override
    def update(self):
        self.compute.dispatch(self.target.width // 8, self.target.height // 8, 1)
        self.swapchain.present(self.target)  # pyright: ignore[reportOptionalMemberAccess]

    @cached_property
    def staging(self) -> compushady.Buffer:
        return compushady.Buffer(self.COUNT * 2 * sizeof(c_int), compushady.HEAP_UPLOAD)

    @cached_property
    def points_buffer(self) -> compushady.Buffer:
        return compushady.Buffer(size=self.staging.size, format=R32G32_UINT)

    def update_buffer(self):
        self.staging.upload(
            struct.pack(f"{self.COUNT * 2}i", *map(int, flatten(*self.points)))
        )
        self.staging.copy_to(self.points_buffer)

    def generate_points(self) -> None:
        self.points = [
            Vector2(uniform(0, app.window.width), uniform(0, app.window.height))
            for _ in range(self.COUNT)
        ]

        self.update_buffer()


app.mainloop()
```

For a different example using [zengl](https://github.com/szabolcsdombi/zengl/), see [this](https://github.com/INCOHESIONS/sky-engine/blob/main/examples/hello_triangle.py) in the [examples](https://github.com/incohesions/sky-engine/tree/main/examples) folder.
