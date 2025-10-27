import pygame

from sky import App

app = App()
app.events.cancel(pygame.QUIT, when="always")
app.mainloop()
