import os
from datetime import datetime, timedelta
from typing import override

import pygame

from ..core import Component

if os.name == "nt":
    import win32api

__all__ = ["Chrono"]


class Chrono(Component):
    """Handles time."""

    def __init__(self) -> None:
        self.start_time = None
        """The time the app started, or None if it hasn't started yet."""

        self.stop_time = None
        """The time the app stopped, or None if it hasn't stopped yet."""

        self.target_framerate = self._get_main_monitor_refrate()
        """The target framerate. Set to 0 to disable framerate limiting. Set to the main monitor's refresh rate by default, or 60 if not on Windows."""

        self.deltatime = 0
        """The time since the last frame."""

        self.framerate = 0
        """The current framerate."""

        self.frames = 0
        """The number of frames since the start of the app."""

        self._internal_clock = pygame.time.Clock()

    @property
    def time_since_start(self) -> timedelta | None:
        """The time since the start of the app, or None if it hasn't started yet."""

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
        self.framerate = self._internal_clock.get_fps()
        self.frames += 1

    def _get_main_monitor_refrate(self) -> float:
        if os.name == "nt":
            device = win32api.EnumDisplayDevices(DevNum=0)
            settings = win32api.EnumDisplaySettings(device.DeviceName, -1)
            return settings.DisplayFrequency

        return 60
