# Based on Unity's Coroutines. See https://docs.unity3d.com/6000.2/Documentation/Manual/Coroutines.html for more

from sky import App, Coroutine
from sky.colors import BLUE, RED
from sky.utils import animate

app = App()


@app.setup
def lerp_color() -> Coroutine:
    for t in animate(duration=3, step=lambda: app.chrono.deltatime):
        app.window.surface.fill(RED.lerp(BLUE, t))
        yield None  # same as WaitForFrames(1)


app.mainloop()
