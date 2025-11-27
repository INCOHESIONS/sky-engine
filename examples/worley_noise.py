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
