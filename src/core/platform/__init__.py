from src.core.platform.capabilities import (
    LANGUAGES,
    OCR_ENGINES,
    OCR_LANG_MAPPING,
    SCREENSHOT_ENGINES,
    TRANSLATION_ENGINES,
)
from src.core.platform.system_info import (
    SystemInfo,
    get_compositor,
    get_desktop_environment,
    get_os,
)

__all__ = [
    "LANGUAGES",
    "OCR_ENGINES",
    "OCR_LANG_MAPPING",
    "SCREENSHOT_ENGINES",
    "SystemInfo",
    "TRANSLATION_ENGINES",
    "get_compositor",
    "get_desktop_environment",
    "get_os",
]
