"""Contains the `Chrono` component that handles time."""

from datetime import datetime, timedelta
from typing import final, override

import pygame

from ..core import Component

__all__ = ["Chrono"]


@final
class Chrono(Component):
    """Handles time."""

    def __init__(self) -> None:
        self.start_time = None
        """The time the app started, or None if it hasn't started yet."""

        self.stop_time = None
        """The time the app stopped, or None if it hasn't stopped yet."""

        self.target_framerate = self.app.windowing.primary_monitor.refresh_rate
        """The target framerate. Set to 0 to disable framerate limiting. Set to the main monitor's refresh rate by default."""

        self.deltatime = 0
        """The time since the last frame."""

        self.framerate = 0
        """The current framerate."""

        self.frames = 0
        """The number of frames since the start of the app."""

        self.min_fps = 0
        """The minimum framerate achieved since the start of the app."""

        self.max_fps = 0
        """The maximum framerate achieved since the start of the app."""

        self._internal_clock = pygame.time.Clock()

    @property
    def time_since_start(self) -> timedelta | None:
        """The time since the start of the app, or None if it hasn't started yet."""

        return datetime.now() - self.start_time if self.start_time else None

    @property
    def avg_fps(self) -> float:
        """The average framerate achieved since the start of the app."""

        return (
            self.frames / self.time_since_start.total_seconds()
            if self.time_since_start is not None
            else 0
        )

    @override
    def start(self) -> None:
        self.start_time = datetime.now()

    @override
    def stop(self) -> None:
        self.stop_time = datetime.now()

    @override
    def update(self) -> None:
        self.deltatime = self._internal_clock.tick(self.target_framerate) / 1000
        self.framerate = self._internal_clock.get_fps()
        self.frames += 1

        if self.framerate < self.min_fps:
            self.min_fps = self.framerate
        if self.framerate > self.max_fps:
            self.max_fps = self.framerate
