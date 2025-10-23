# pyright: reportUninitializedInstanceVariable=false

# Based on https://github.com/pygame-community/pygame-ce/blob/main/examples/window_opengl.py

from typing import override

import zengl

from sky import App, Component, WindowSpec


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
            app.window.size.to_int_tuple(), "rgba8unorm", samples=4
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


app = App(spec=WindowSpec(backend="opengl"))
app.add_component(RenderPipeline)
app.mainloop()
