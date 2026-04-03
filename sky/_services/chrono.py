from datetime import datetime, timedelta
from typing import final, override

from pygame import Clock

from ..core import Service

__all__ = ["Chrono"]


@final
class Chrono(Service):
    """Handles time-related data."""

    def __init__(self) -> None:
        self.target_framerate = self.app.windowing.primary_monitor.refresh_rate
        """The target framerate. Set to 0 to disable framerate limiting. Set to the main monitor's refresh rate by default."""

        self.framerate = 0
        """The current framerate."""

        self.min_framerate = 0
        """The minimum framerate achieved since the start of the app."""

        self.max_framerate = 0
        """The maximum framerate achieved since the start of the app."""

        self.frames = 0
        """The number of frames since the start of the app."""

        self.deltatime = 0
        """The time since the last frame."""

        self.start_time = None
        """The time the app started, or None if it hasn't started yet."""

        self.stop_time = None
        """The time the app stopped, or None if it hasn't stopped yet."""

        self._clock = Clock()

    @property
    def clock(self) -> Clock:
        """The internal clock that keeps track of and manages framerate."""

        return self._clock

    @property
    def time_since_start(self) -> timedelta | None:
        """The time since the start of the app, or None if it hasn't started yet."""

        return datetime.now() - self.start_time if self.start_time else None

    @property
    def time_since_stopped(self) -> timedelta | None:
        """The time since the moment the app stopped running, or None if it hasn't stopped yet."""

        return datetime.now() - self.stop_time if self.stop_time else None

    @override
    def start(self) -> None:
        self.start_time = datetime.now()

    @override
    def stop(self) -> None:
        self.stop_time = datetime.now()

    @override
    def update(self) -> None:
        self.deltatime = self._clock.tick(self.target_framerate) / 1000
        self.framerate = self._clock.get_fps()

        self.min_framerate = min(self.framerate, self.min_framerate)
        self.max_framerate = max(self.framerate, self.max_framerate)

        self.frames += 1
