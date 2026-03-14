from sky import App, Hook
from sky.utils import discard

app = App()

some_event = Hook(cancellable=True)


@some_event
def some_event1() -> None:
    print("This will print.")
    some_event.cancel()


@some_event
def some_event2() -> None:
    print("This will not print.")


app.on_setup += lambda: discard(some_event.invoke())

app.mainloop()
