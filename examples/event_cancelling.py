import pygame

from sky import App

app = App()


@app.pre_update
def pre_handling() -> None:
    # prevents the app from closing. use CTRL + C on your terminal instead
    app.events.cancel(pygame.QUIT)


app.mainloop()
