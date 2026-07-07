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
    resolve_capabilities,
)
from src.core.platform.system_info import (
    SystemInfo,
    get_compositor,
    get_desktop_environment,
    get_os,
)

__all__ = [
    "CONFIG_DIR",
    "LANGUAGES",
    "OCR_ENGINES",
    "OCR_LANG_MAPPING",
    "PORTAL_ORIENTATION",
    "SCREENSHOT_ENGINES",
    "SETTINGS_TOPMOST_HOTKEY",
    "TEMPORARY_REGION_HOTKEY",
    "SystemInfo",
    "TRANSLATION_ENGINES",
    "get_compositor",
    "get_desktop_environment",
    "get_os",
    "resolve_capabilities",
]
