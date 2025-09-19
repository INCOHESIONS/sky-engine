from datetime import datetime, timedelta
from typing import override

import pygame

from ..core import Component

__all__ = ["Chrono"]


class Chrono(Component):
    def __init__(self) -> None:
        self.start_time = None
        self.stop_time = None

        self.target_framerate = 60
        self.deltatime = 0
        self.frames = 0

        self._internal_clock = pygame.time.Clock()

    @property
    def time_since_start(self) -> timedelta | None:
        if self.start_time is None:
            return None
        return datetime.now() - self.start_time

    @override
    def start(self) -> None:
        self.start_time = datetime.now()

    @override
    def stop(self) -> None:
        self.stop_time = datetime.now()

    @override
    def update(self) -> None:
        self.deltatime = self._internal_clock.tick(self.target_framerate) / 1000
        self.frames += 1
