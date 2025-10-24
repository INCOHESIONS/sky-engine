"""
Sky Engine
----------

A wrapper around `pygame` that makes it less painful to use.

:copyright: (c) 2025 by iNCOHESiONS.
:license: MIT, see LICENSE for more details.
"""

__title__ = "sky-engine"
__description__ = "A wrapper around pygame that makes it less painful to use."
__url__ = "https://github.com/incohesions/sky-engine"
__author__ = "iNCOHESiONS"
__version__ = "0.0.1"
__license__ = "MIT"


from os import environ

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "true"

del environ

import pygame

from .app import App
from .core import AppSpec, Component, Keybinding, WindowSpec
from .enums import Cursor, Key, MouseButton, State
from .hook import Hook
from .types import Coroutine
from .utils import Color, Vector2
from .yieldable import WaitForFrames, WaitForSeconds, WaitUntil, WaitWhile

if not getattr(pygame, "IS_CE", False):
    print(
        "Please use pygame-ce (https://pypi.org/project/pygame-ce/) instead of pygame."
    )
    exit(-1)

__all__ = [
    "App",
    "AppSpec",
    "Color",
    "Component",
    "Coroutine",
    "Cursor",
    "Hook",
    "Key",
    "Keybinding",
    "MouseButton",
    "State",
    "Vector2",
    "WaitForFrames",
    "WaitForSeconds",
    "WaitUntil",
    "WaitWhile",
    "WindowSpec",
]
