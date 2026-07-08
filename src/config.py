import os
import tempfile

APP_VERSION = "0.1.5"

from src.core.platform.capability_resolver import (
    CONFIG_DIR,
    LANGUAGES,
    OCR_ENGINES,
    OCR_LANG_MAPPING,
    PORTAL_ORIENTATION,
    SCREENSHOT_ENGINES,
    SETTINGS_TOPMOST_HOTKEY,
    TEMPORARY_REGION_HOTKEY,
    TRANSLATION_ENGINES,
)
from src.core.platform.system_info import (
    get_compositor,
    get_desktop_environment,
    get_os,
)

OS = get_os()
DESKTOP_ENVIRONMENT = get_desktop_environment()
COMPOSITOR = get_compositor()

DPI_SCALE_DEFAULT = 1.0  # Auto-detected from QScreen.devicePixelRatio, user can override

if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR, exist_ok=True)

SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.pkl")
PRESETS_FILE = os.path.join(CONFIG_DIR, "presets.pkl")

# Temp Files
TEMP_DIR = tempfile.gettempdir()
DEV_SHM ="/dev/shm"
IMG_PATH = os.path.join(DEV_SHM, "usta_snapshot.jpeg")
FULL_SCREEN_TEMP_PATH = os.path.join(DEV_SHM, "usta_full_snap.jpeg")
SOCKET_PATH = os.path.join(TEMP_DIR, "usta.sock")
SLURP_TEMP_PATH = os.path.join(TEMP_DIR, "slurp_final.txt")
