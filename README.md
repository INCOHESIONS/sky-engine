# Sky Engine

More like a wrapper than an engine. Makes `pygame` less painful to use. Fully typed with Pylance on strict mode. Probably won't actually publish this on PyPI, but it's here for now.

Rendering is yet to be implemented, and thus is up to the user. An OpenGL example is provided below using `zengl`, but you can also use `pygame`'s software renderer with `pygame.draw`.

## Usage

Simple example:

```python
from sky import App

app = App()

# pre component (i.e. windowing, keyboard) update
@app.pre_update
def pre_update() -> None:
    print("Runs every frame!")


@app.keyboard.on_key
def on_key(key: Key, state: State) -> None:
    print(f"Key {key} was {state.name}!")  # states: pressed (held down for more than one frame), downed (just pressed), released (just released)


# alternatively, you can add keybindings instead of listening for events
app.keyboard.add_keybindings({
    Key.escape: app.quit,
    Key.f11: app.windowing.toggle_fullscreen,
})  # fmt: skip

app.mainloop()
```

Rendering example (using [zengl](https://github.com/szabolcsdombi/zengl), based on [this](https://github.com/bilhox/pygame-ce/blob/main/examples/window_opengl.py) pygame-ce example):

```py
from typing import override

import zengl

from sky import App, AppSpec, Backend, Component, WindowSpec


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


spec = AppSpec(window_spec=WindowSpec(backend=Backend.opengl))
app = App(spec=spec)
app.add_component(RenderPipeline).mainloop()
```

Coroutine example:

```python
from sky import App, WaitForSeconds
from sky.colors import BLUE, RED
from sky.types import Coroutine

app = App()


@app.setup
def change_bg_color() -> Coroutine:
    assert app.windowing.surface is not None
    app.windowing.surface.fill(RED)
    yield WaitForSeconds(3)
    app.windowing.surface.fill(BLUE)


app.mainloop()
```
