"""macOS capability overrides.

Only define values here when they differ from src.core.platform.capabilities.
"""

import os


SCREENSHOT_ENGINES = ["MacOS"]

CONFIG_DIR = os.path.join(
    os.path.expanduser("~"),
    "Library",
    "Application Support",
    "usta",
)
