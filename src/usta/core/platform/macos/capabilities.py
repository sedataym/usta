"""macOS capability overrides.

Only define values here when they differ from usta.core.platform.capabilities.
"""

import os

from usta.core.platform.capabilities import OCR_ENGINES as BASE_OCR_ENGINES

OCR_ENGINES = [*BASE_OCR_ENGINES, "Apple Vision"]

SCREENSHOT_ENGINES = ["MacOS"]

CONFIG_DIR = os.path.join(
    os.path.expanduser("~"),
    "Library",
    "Application Support",
    "usta",
)
