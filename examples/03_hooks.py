from pygame import draw

from sky import App, WindowSpec
from sky.colors import ALICE_BLUE, CRIMSON

app = App(spec=WindowSpec(fill=CRIMSON))


@app.on_setup
def setup() -> None:
    print("This will run as the app starts.")


@app.pre_update
def pre_update() -> None:
    print("This will run every frame.")


@app.window.on_render
def on_render1() -> None:
    print(
        "This will also run every frame, but is tied to a certain Window. Use this for rendering!"
    )


@app.on_render
def on_render2() -> None:
    print("Alternatively, use the alias `app.on_render`.")
    draw.aacircle(app.window.surface, ALICE_BLUE, app.window.center, 32)


@app.on_cleanup
def cleanup() -> None:
    print("This will run as soon as the app finishes running.")


app.mainloop()
