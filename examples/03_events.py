from pygame import draw

from sky import App, WindowSpec
from sky.colors import ALICE_BLUE, CRIMSON

app = App(spec=WindowSpec(fill=CRIMSON))


@app.setup
def setup() -> None:
    print("This will run as the app starts.")


@app.pre_update
def pre_update() -> None:
    print("This will run every frame.")


@app.window.on_render
def on_render() -> None:
    print(
        "This will also run every frame, but is tied to a certain Window. Use this for rendering!"
    )

    draw.aacircle(app.window.surface, ALICE_BLUE, app.window.center, 32)


@app.cleanup
def cleanup() -> None:
    print("This will run as soon as the app finishes running.")


app.mainloop()
