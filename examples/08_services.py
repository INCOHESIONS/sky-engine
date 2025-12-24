from typing import override

from sky import App, Service

app = App()


class SomeService(Service):
    @override
    def update(self) -> None:
        print("Runs every frame!")


app.add_service(SomeService())
app.mainloop()
