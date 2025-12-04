from pygame import draw

from sky import App, Key, MouseButton, WindowSpec
from sky.colors import ALICE_BLUE, CRIMSON

app = App(spec=WindowSpec(fill=CRIMSON))

pos = app.window.center
speed = 2
radius = 32


@app.window.on_render
def render():
    global pos
    pos += app.keyboard.get_movement_2d((Key.a, Key.d), (Key.w, Key.s)) * speed
    draw.aacircle(app.window.surface, ALICE_BLUE, pos, radius)


@app.mouse.on_mouse_button_downed
def change_radius(button: MouseButton) -> None:
    global radius
    radius += -1 if button == MouseButton.right else 1


app.mainloop()
