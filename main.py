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
