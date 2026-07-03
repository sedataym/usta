"""Linux capability overrides.

Only define values here when they differ from src.core.platform.capabilities.
"""

import os


CONFIG_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config")),
    "usta",
)
