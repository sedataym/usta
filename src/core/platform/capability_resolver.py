import importlib
from types import ModuleType
from typing import Any, Iterable, Optional

from src.core.platform import capabilities as base_capabilities
from src.core.platform.system_info import get_desktop_environment, get_os


CAPABILITY_NAMES = (
    "OCR_ENGINES",
    "TRANSLATION_ENGINES",
    "SCREENSHOT_ENGINES",
    "LANGUAGES",
    "OCR_LANG_MAPPING",
    "PORTAL_ORIENTATION",
    "SETTINGS_TOPMOST_HOTKEY",
    "CONFIG_DIR",
)


def _normalize_module_part(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return normalized or None


def _get_platform_package(os_name: Optional[str]) -> Optional[str]:
    normalized_os = _normalize_module_part(os_name)
    if normalized_os == "linux":
        return "linux"
    if normalized_os == "darwin":
        return "macos"
    if normalized_os == "windows":
        return "windows"

    return normalized_os


def _import_optional_module(module_name: str) -> Optional[ModuleType]:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name or module_name.startswith(f"{exc.name}."):
            return None
        raise


def _iter_capability_modules(
    os_name: Optional[str] = None,
    desktop_environment: Optional[str] = None,
) -> Iterable[ModuleType]:
    platform_package = _get_platform_package(os_name)
    if platform_package is None:
        return

    module_names = [f"src.core.platform.{platform_package}.capabilities"]
    if platform_package == "linux":
        desktop_package = _normalize_module_part(desktop_environment)
        if desktop_package is not None:
            module_names.append(f"src.core.platform.linux.{desktop_package}.capabilities")

    for module_name in module_names:
        module = _import_optional_module(module_name)
        if module is not None:
            yield module


def get_capability(name: str, default: Any = None) -> Any:
    return globals().get(name, default)


def resolve_capabilities(
    os_name: Optional[str] = None,
    desktop_environment: Optional[str] = None,
) -> dict[str, Any]:
    os_name = get_os() if os_name is None else os_name
    desktop_environment = (
        get_desktop_environment() if desktop_environment is None else desktop_environment
    )

    resolved = {name: getattr(base_capabilities, name) for name in CAPABILITY_NAMES}
    for module in _iter_capability_modules(os_name, desktop_environment):
        for name in CAPABILITY_NAMES:
            if hasattr(module, name):
                resolved[name] = getattr(module, name)

    return resolved


_RESOLVED_CAPABILITIES = resolve_capabilities()

OCR_ENGINES = _RESOLVED_CAPABILITIES["OCR_ENGINES"]
TRANSLATION_ENGINES = _RESOLVED_CAPABILITIES["TRANSLATION_ENGINES"]
SCREENSHOT_ENGINES = _RESOLVED_CAPABILITIES["SCREENSHOT_ENGINES"]
LANGUAGES = _RESOLVED_CAPABILITIES["LANGUAGES"]
OCR_LANG_MAPPING = _RESOLVED_CAPABILITIES["OCR_LANG_MAPPING"]
PORTAL_ORIENTATION = _RESOLVED_CAPABILITIES["PORTAL_ORIENTATION"]
SETTINGS_TOPMOST_HOTKEY = _RESOLVED_CAPABILITIES["SETTINGS_TOPMOST_HOTKEY"]
CONFIG_DIR = _RESOLVED_CAPABILITIES["CONFIG_DIR"]
