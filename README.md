# Sky Engine

Makes `pygame` (or rather, [pygame-ce](https://github.com/pygame-community/pygame-ce), more specifically) less painful to use. More like a wrapper than an engine. Fully typed with [basedpyright](https://github.com/DetachHead/basedpyright).

> Theoretically cross-platform, but mostly tested on Windows. May have some window manager weirdness on Linux, specifically when it comes to fullscreening.

## Quick Start

Due to the engine's many defaults, only 2 lines of code are required to get started. This opens an 800x600 window, centered on the main monitor, with a black background:

```python
from sky import App

App().mainloop()
```

To modify the app's defaults, including the default window's properties, one may use the `spec` argument:
```python
from sky import App, AppSpec, Vector2, WindowSpec
from sky.colors import CRIMSON

app = App(
    spec=AppSpec(
        window_spec=WindowSpec(title="My Window", size=Vector2(400, 400), fill=CRIMSON)
    )
)

app.mainloop()
```

For a headless `App`, one may simply set `window_spec` to None, or use the `AppSpec.headless()` classmethod.

`Sky` provides users many `Hook`s that may contain callbacks to be executed whenever the `Hook` is triggered. They can be used as decorators, which makes for particularly elegant code:

```python
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
```

> Note: although `Sky` itself doesn't favor any particular module or form of rendering, we will use `pygame.draw` for examples, as it comes bundled with `pygame`. For examples that perform hardware rendering using other libraries, see the [examples](https://github.com/INCOHESIONS/sky-engine/tree/main/examples) folder.

`Hook`s may also have their execution cancelled. The following example prevents the window and the app from closing:

```python
import pygame

from sky import App

app = App()

app.events.cancel(pygame.WINDOWCLOSE, when="always")
app.events.cancel(pygame.QUIT, when="always")

app.mainloop()
```

Combining `Hook`s, `Spec`s, and rendering, we can create two windows with differently colored backgrounds that render differently colored circles to their surfaces:

```python
from pygame import draw

from sky import App, AppSpec, Color, Window, WindowSpec
from sky.colors import CRIMSON, DODGER_BLUE
from sky.utils import discard

app = App(spec=AppSpec.headless())

window1 = app.windowing.add_window(spec=WindowSpec(title="Window 1", fill=CRIMSON))
window2 = app.windowing.add_window(spec=WindowSpec(title="Window 2", fill=DODGER_BLUE))


def render_to(window: Window, color: Color) -> None:
    window.on_render += lambda: discard(
        draw.aacircle(window.surface, color, window.center, 32)
    )


render_to(window1, DODGER_BLUE)
render_to(window2, CRIMSON)


app.mainloop()
```

To allow for interactions by grabbing user input, users may utilize the `mouse` and `keyboard` services. With them, we can render a circle to the screen that moves according to the player's WASD input, and changes size with the right and left mouse buttons:

```python
from pygame import draw

from sky import App, MouseButton, WindowSpec
from sky.colors import ALICE_BLUE, CRIMSON

app = App(spec=WindowSpec(fill=CRIMSON))
app.keyboard.add_keybindings(escape=app.quit)

pos = app.window.center
speed = 2
radius = 32


@app.window.on_render
def render():
    global pos
    pos += app.keyboard.get_movement_2d(("a", "d"), ("w", "s")) * speed
    draw.aacircle(app.window.surface, ALICE_BLUE, pos, radius)


@app.mouse.on_mouse_button_downed
def change_radius(button: MouseButton) -> None:
    global radius
    radius += -1 if button == MouseButton.right else 1


app.mainloop()
```

Using globals for everything is bad practice, however. Using `Component`s, we can rewrite the example above, packaging everything into a single object:

```python
from dataclasses import dataclass, field
from typing import override

from pygame import draw

from sky import App, Component, MouseButton, Vector2, WindowSpec
from sky.colors import ALICE_BLUE, CRIMSON

app = App(spec=WindowSpec(fill=CRIMSON))
app.keyboard.add_keybindings(escape=app.quit)


@dataclass
class Player(Component):
    pos: Vector2 = field(default_factory=lambda: app.window.center)
    speed: float = 2
    radius: int = 32

    @override
    def start(self) -> None:
        app.mouse.on_mouse_button_downed += self.change_radius

    @override
    def update(self) -> None:
        self.pos += app.keyboard.get_movement_2d(("a", "d"), ("w", "s")) * self.speed
        draw.aacircle(app.window.surface, ALICE_BLUE, self.pos, self.radius)

    def change_radius(self, button: MouseButton) -> None:
        self.radius += -1 if button == MouseButton.right else 1


app.add_component(Player)
app.mainloop()
```

Since `Player` has defaults for all of its constructor parameters, we may pass the type directly into `add_component`, letting the app instance it for us. Alternatively, if one is building a singleplayer game, or has some sort of "game controller" class that contains shared logic or data, they may use the `@app.singleton_component` decorator, making the class declaration look like this:

```python
@app.singleton_component  # has to come before @dataclass
@dataclass
class Player(Component):
    ...
```

The decorator immediately instances the class, and adds it to the app. It also makes the decorated class a singleton, and as such any subsequent instantiations will always refer to the same object:

```python
assert Player() is Player()  # passes
```

Notably, these examples use `app.mouse` and `app.keyboard`, which are `Service`s, `Service`s are objects that offer persistant, generalized functionality, and have an `update` method that runs every frame. By default, the engine offers 7 `Service`s:
- `Events` (handles `pygame` events)
- `Keyboard` (handles keyboard input)
- `Mouse` (handles mouse input)
- `Windowing` (handles windowing)
- `Chrono` (handles time-related data)
- `Executor` (handles coroutines)
- `UI` (handles the user interface)

Users may add their own `Service`s by subclassing the `Service` class, and using the `add_service` method:
```python
from typing import override

from sky import App, Service

app = App()


class SomeService(Service):
    @override
    def update(self) -> None:
        print("Runs every frame!")


app.add_service(SomeService())
app.mainloop()
```

So far, we've used methods that run either at the start, or at every frame. But many games require more granular control over timing, using delays, loops and animations for a better user experience. `Coroutine`s are the engine's way of handling such tasks.

```python
from sky import App, Coroutine
from sky.colors import CRIMSON, DODGER_BLUE
from sky.utils import Color, animate

app = App()


@app.setup
def lerp_color() -> Coroutine:
    for t in animate(duration=3, step=lambda: app.chrono.deltatime):
        app.window.fill_color = Color(CRIMSON.lerp(DODGER_BLUE, t))
        yield None  # same as WaitForFrames(1)


app.mainloop()
```

`Hook`s can automatically detect `Coroutine`s, calling `app.executor.start_coroutine` when triggered instead of simply calling the decorated generator function.

> The use of generators and `yield` was heavily inspired by `Unity`. See their [documentation](https://docs.unity3d.com/6000.2/Documentation/Manual/Coroutines.html) for their version of the feature, done in `C#`.

Earlier, we'd called `add_component` directly on our `app` instance. Doing this actually calls `add_component` on the most recently added `Scene`, the engine's way of organizing many components into separate objects for easier management. Multiple `Scene`s may be loaded at once, as games usually contain portions that act differently from others, but are ran concurrently, such as the level and user interface.

In our case, the most recently added `Scene` is simply the default scene, as we haven't added any others. Here's an example that does not create a default scene, and instead adds two scenes, with each rendering a differently colored circle:

```python
from dataclasses import dataclass
from typing import override

from pygame import draw

from sky import App, AppSpec, Color, Component, Scene, Vector2
from sky.colors import BLUE, RED

app = App(spec=AppSpec.sceneless())  # no default scene since we'll add our own


@dataclass
class Circle(Component):
    pos: Vector2
    color: Color

    @override
    def update(self):
        draw.aacircle(app.window.surface, self.color, self.pos, 50)


app.load_scene(
    red_scene := Scene.from_components(
        [Circle(app.window.center + Vector2(100, 0), BLUE)]
    )
)
app.load_scene(
    blue_scene := Scene.from_components(
        [Circle(app.window.center - Vector2(100, 0), RED)]
    )
)

app.keyboard.add_keybindings(
    a=lambda: app.toggle_scene(blue_scene), b=lambda: app.toggle_scene(red_scene)
)

app.mainloop()
```

This README covers most of the engine's main features, but one may dig through the source code and extra examples to learn more. Do note that this project is in heavy active development and breaking changes occur constantly, so don't use it for anything serious.
