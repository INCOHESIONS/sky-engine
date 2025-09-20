"""
Sky Engine
----------

A wrapper around pygame that makes it less painful to use.

:copyright: (c) 2025 by iNCOHESiONS.
:license: MIT, see LICENSE for more details.
"""

__title__ = "sky-engine"
__description__ = "A wrapper around pygame that makes it less painful to use."
__author__ = "iNCOHESiONS"
__version__ = "0.0.1"
__url__ = "https://github.com/incohesions/sky-engine"
__license__ = "MIT"


from os import environ

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "true"

del environ

import pygame

from .app import App
from .core import Component, WaitForFrames, WaitForSeconds, WaitUntil, WaitWhile
from .enums import Cursor, Key, MouseButton, State
from .listenable import Listenable
from .spec import AppSpec, WindowSpec
from .utils import Color, Vector2

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
    "Cursor",
    "Key",
    "Listenable",
    "MouseButton",
    "State",
    "Vector2",
    "WaitForFrames",
    "WaitForSeconds",
    "WaitUntil",
    "WaitWhile",
    "WindowSpec",
]
