import importlib
import inspect
import sys
from collections.abc import Iterable
from functools import cached_property
from operator import itemgetter
from pathlib import Path
from types import ModuleType
from typing import final, override

from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from sky import App, Component, Module
from sky.utils import filter_by_attrs

__all__ = ["HotReload", "hot_reloadable"]


@final
class _HotReloadEventHandler(FileSystemEventHandler):
    @cached_property
    def _app(self) -> App:
        return App()

    @override
    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if isinstance(event, DirModifiedEvent):
            return

        path = Path(str(event.src_path))

        if path.suffix != ".py":
            return

        name = path.with_suffix("").name
        mod = importlib.reload(sys.modules[name])

        for cls in filter(self._is_hot_reloadable, self._get_classes(module=mod)):
            for component in self._app.get_components(cls.__name__):
                component.__class__ = cls

    def _is_hot_reloadable(self, cls: type, /) -> bool:
        return getattr(cls, "__hot_reloadable__", False) and Component in cls.__bases__

    def _get_classes(self, /, *, module: ModuleType) -> Iterable[type]:
        return filter_by_attrs(
            map(itemgetter(1), inspect.getmembers(module, inspect.isclass)),
            __module__=module.__name__,
        )


@final
class HotReload(Module):
    """Module that adds support for hot reloading `Component`s from the specified directory."""

    def __init__(
        self, /, *, directory: Path | str = ".", recursive: bool = True
    ) -> None:
        if isinstance(directory, Path):
            assert directory.is_dir()
            directory = directory.as_posix()

        self.observer = Observer()
        self.observer.schedule(
            _HotReloadEventHandler(),
            directory,
            recursive=recursive,
            event_filter=[FileModifiedEvent],
        )

    @override
    def init(self) -> None:
        self.observer.start()

    @override
    def quit(self) -> None:
        self.observer.stop()


def hot_reloadable[C: type[Component]](cls: C, /) -> C:
    """
    Makes a `Component` hot reloadable.

    Parameters
    ----------
    cls: `C`
        The decorated type; must be a subclass of `Component`.

    Returns
    -------
    cls: `C`
        The decorated type, now hot reloadable.
    """

    assert issubclass(cls, Component)
    cls.__hot_reloadable__ = True
    return cls
