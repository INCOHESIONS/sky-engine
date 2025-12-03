from sky import App, AppSpec, Vector2, WindowSpec
from sky.colors import CRIMSON

app = App(
    spec=AppSpec(
        window_spec=WindowSpec(title="My Window", size=Vector2(400, 400), fill=CRIMSON)
    )
)


app.mainloop()
