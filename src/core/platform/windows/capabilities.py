"""Windows capability overrides.

Only define values here when they differ from src.core.platform.capabilities.
"""

import os


CONFIG_DIR = os.path.join(
    os.environ.get(
        "APPDATA",
        os.path.join(os.path.expanduser("~"), "AppData", "Roaming"),
    ),
    "UmayOCR",
)
