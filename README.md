# Sky Engine

More like a wrapper than an engine. Makes `pygame` less painful to use. Fully typed with Pylance on strict mode.

Generally cross-platform, but mostly tested on Windows. May have some window manager weirdness on Linux, specifically when it comes to fullscreening.

Rendering is yet to be implemented, and thus is up to the user. An OpenGL example is provided below using `zengl`, as well as one using `pygame`'s software renderer with `pygame.draw`.

## Usage

Rendering example (using [zengl](https://github.com/szabolcsdombi/zengl), based on [this](https://github.com/bilhox/pygame-ce/blob/main/examples/window_opengl.py) pygame example):

```py
from typing import override

import zengl

from sky import App, AppSpec, Component, WindowSpec


class RenderPipeline(Component):
    VERTEX_SHADER = """
        #version 330 core

        out vec3 v_color;

        vec2 vertices[3] = vec2[](
            vec2(0.0, 0.8),
            vec2(-0.6, -0.8),
            vec2(0.6, -0.8)
        );

        vec3 colors[3] = vec3[](
            vec3(1.0, 0.0, 0.0),
            vec3(0.0, 1.0, 0.0),
            vec3(0.0, 0.0, 1.0)
        );

        void main() {
            gl_Position = vec4(vertices[gl_VertexID], 0.0, 1.0);
            v_color = colors[gl_VertexID];
        }
    """

    FRAGMENT_SHADER = """
        #version 330 core

        in vec3 v_color;

        layout (location = 0) out vec4 out_color;

        void main() {
            out_color = vec4(v_color, 1.0);
            out_color.rgb = pow(out_color.rgb, vec3(1.0 / 2.2));
        }
    """

    @override
    def start(self) -> None:
        self._ctx = zengl.context()
        self._image = self._ctx.image(
            app.windowing.size.to_int_tuple(), "rgba8unorm", samples=4
        )
        self._pipeline = self._ctx.pipeline(
            vertex_shader=self.VERTEX_SHADER,
            fragment_shader=self.FRAGMENT_SHADER,
            framebuffer=[self._image],
            topology="triangles",
            vertex_count=3,
        )

    @override
    def update(self) -> None:
        self._ctx.new_frame()
        self._image.clear()
        self._pipeline.render()
        self._image.blit()
        self._ctx.end_frame()


spec = AppSpec(window_spec=WindowSpec(backend="opengl"))

app = App(spec=spec)
app.add_component(RenderPipeline)
app.mainloop()
```

More involved, interactive example (using pygame's drawing functions):

```py
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
    acceleration: Vector2
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
```

Coroutine example (based on [Unity's coroutines](https://docs.unity3d.com/6000.2/Documentation/Manual/Coroutines.html)):

```python
from sky import App
from sky.colors import BLUE, RED
from sky.types import Coroutine
from sky.utils import animate

app = App()


@app.setup
def lerp_color() -> Coroutine:
    assert app.windowing.surface is not None

    for t in animate(duration=3, step=lambda: app.chrono.deltatime):
        app.windowing.surface.fill(RED.lerp(BLUE, t))
        yield None  # same as WaitForFrames(1)


app.mainloop()
```
