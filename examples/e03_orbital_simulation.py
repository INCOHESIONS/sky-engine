# Based on https://github.com/AstroKhet/Orbit-Simulator-2D/

from dataclasses import KW_ONLY, dataclass, field
from math import atan2, cos, sin
from typing import override

from pygame import draw as render
from pygame import freetype

from sky import App, AppSpec, Color, Component, MouseButton, Vector2, WindowSpec
from sky.colors import WHITE
from sky.utils import mapl

app = App(
    spec=AppSpec(
        window_spec=WindowSpec(state="maximized", resizable=True), modules=[freetype]
    )
)

app.keyboard.add_keybindings(escape=app.quit, f11=app.window.toggle_fullscreen)

font = freetype.SysFont("Arial", 16)

G = 6.674e-11

ITERATIONS = 100
STEP_SIZE = 1000

TRAJECTORY_LENGTH = 1000

camera_pos = Vector2()
scale = 1e9


@app.on_setup
def focus_sun() -> None:
    global camera_pos
    camera_pos = -sun.display_pos + app.window.center


@app.mouse.on_mouse_button_pressed.equals(MouseButton.left)
def on_mouse_button_pressed() -> None:
    global camera_pos
    camera_pos += app.mouse.velocity


@app.mouse.on_mouse_wheel
def on_mouse_wheel(delta: Vector2) -> None:
    global scale
    scale -= scale / 10 * delta.y


app.window.on_resize.add_callback(lambda _: focus_sun())
app.window.on_fullscreen.add_callback(lambda _: focus_sun())
app.mouse.on_mouse_wheel.add_callback(lambda _: focus_sun())


@dataclass
class AstronomicalObject(Component):
    _: KW_ONLY

    pos: Vector2 = field(default_factory=Vector2)
    vel: Vector2 = field(default_factory=Vector2)
    acc: Vector2 = field(default_factory=Vector2)
    mass: float = 0
    radius: float = 0

    label: str | None = None
    color: Color = field(default_factory=lambda: WHITE)
    scale: float = 0

    _trajectory: list[Vector2] = field(default_factory=list)

    def __post_init__(self) -> None:
        app.mouse.on_mouse_wheel.add_callback(lambda _: self._trajectory.clear())

    @property
    def display_pos(self) -> Vector2:
        return Vector2(self.pos.x, app.window.height * scale - self.pos.y) * (1 / scale)

    @override
    def update(self) -> None:
        self.simulate()
        self.render()

    def simulate(self) -> None:
        for _ in range(ITERATIONS):
            for other in app.get_components(self.__class__):
                if other == self:
                    continue

                direction = other.pos - self.pos
                force = G * other.mass / direction.length_squared()
                theta = atan2(*direction.yx)

                self.acc += force * cos(theta), force * sin(theta)

            self.vel += self.acc * STEP_SIZE
            self.pos += self.vel * STEP_SIZE
            self.acc.clear()

    def render(self) -> None:
        dpos = self.display_pos
        drad = self.radius * self.scale / scale

        render.aacircle(app.window.surface, self.color, dpos + camera_pos, drad)

        if self.label:
            surface, rect = font.render(
                self.label,
                WHITE,
                style=freetype.STYLE_STRONG,
                size=max(drad, 8),
            )
            rect.center = dpos + camera_pos + Vector2(0, drad * 2)
            app.window.blit(surface, rect)

        self._trajectory.insert(0, dpos)

        if len(self._trajectory) > TRAJECTORY_LENGTH:
            self._trajectory.pop()

        if len(self._trajectory) > 2:
            render.aalines(
                app.window.surface,
                self.color.with_alpha(128),
                False,
                mapl(lambda p: p + camera_pos, self._trajectory),
            )


app.add_components(
    sun := AstronomicalObject(
        label="Sun",
        color=Color("#ED781C"),
        pos=Vector2(6e12, 6e12),
        mass=1.989e30,
        radius=6.957e8,
        scale=25,
    ),
    AstronomicalObject(
        label="Mecury",
        color=Color("#A49E9E"),
        pos=sun.pos + Vector2(57.9e9, 0),
        vel=Vector2(0, 47.36e3),
        mass=3.285e23,
        radius=2.4397e6,
        scale=1000,
    ),
    AstronomicalObject(
        label="Venus",
        color=Color("#B97629"),
        pos=sun.pos - Vector2(107.48e9, 0),
        vel=Vector2(0, -35.02e3),
        mass=4.867e24,
        radius=6.0518e6,
        scale=1000,
    ),
    AstronomicalObject(
        label="Earth",
        color=Color("#1F8CCA"),
        pos=sun.pos + Vector2(151.96e9, 0),
        vel=Vector2(0, 29.78e3),
        mass=5.9724e24,
        radius=6.356e6,
        scale=1000,
    ),
    AstronomicalObject(
        label="Mars",
        color=Color("#FF8964"),
        pos=sun.pos - Vector2(250.17e9, 0),
        vel=Vector2(0, -24.07e3),
        mass=64171e23,
        radius=3.3895e6,
        scale=1000,
    ),
    AstronomicalObject(
        label="Jupiter",
        color=Color("#BEAC83"),
        pos=sun.pos + Vector2(754.87e9, 0),
        vel=Vector2(0, 13.06e3),
        mass=1.89819e27,
        radius=6.9911e7,
        scale=200,
    ),
    AstronomicalObject(
        label="Saturn",
        color=Color("#E5C480"),
        pos=sun.pos - Vector2(1.4872e12, 0),
        vel=Vector2(0, -9.68e3),
        mass=5.6834e26,
        radius=5.4364e7,
        scale=200,
    ),
    AstronomicalObject(
        label="Uranus",
        color=Color("#CDF1F4"),
        pos=sun.pos + Vector2(2.9541e12, 0),
        vel=Vector2(0, 6.80e3),
        mass=8.6813e25,
        radius=2.4973e7,
        scale=600,
    ),
    AstronomicalObject(
        label="Neptune",
        color=Color("#3845A5"),
        pos=sun.pos - Vector2(4.495e12, 0),
        vel=Vector2(0, -5.43e3),
        mass=1.02413e26,
        radius=2.4341e7,
        scale=600,
    ),
    AstronomicalObject(
        label="Pluto",
        color=Color("#D1CBBF"),
        pos=sun.pos + Vector2(5.90538e12, 0),
        vel=Vector2(0, 4.67e3),
        mass=1.303e22,
        radius=1.188e6,
        scale=1000,
    ),
)

app.mainloop()
