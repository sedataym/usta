"""Resolve installed resources, including resources from zipped packages."""

import atexit
from contextlib import ExitStack
from functools import lru_cache
from importlib.resources import as_file, files
from pathlib import Path

_contexts = ExitStack()
atexit.register(_contexts.close)


@lru_cache(maxsize=None)
def resource_path(relative: str) -> Path:
    """Keep extracted resources alive until application shutdown."""
    return _contexts.enter_context(as_file(files("usta").joinpath(relative)))
