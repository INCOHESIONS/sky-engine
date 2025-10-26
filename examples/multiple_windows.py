from sky import App, WindowSpec
from sky.colors import BLUE, RED

app = App(spec=WindowSpec(title="Main Window!"))
extra_window = app.windowing.add_window(spec=WindowSpec(title="Extra Window!"))


@app.window.on_render
def render() -> None:
    app.window.surface.fill(RED)


@extra_window.on_render
def extra_render() -> None:
    extra_window.surface.fill(BLUE)


app.mainloop()
