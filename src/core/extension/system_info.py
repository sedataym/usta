import os
import platform
import subprocess
from typing import Optional


_COMPOSITOR_PROCESSES = {
    "kwin_wayland": "kwin",
    "kwin_x11": "kwin",
    "kwin": "kwin",
    "mutter": "mutter",
    "gnome-shell": "mutter",
    "picom": "picom",
    "sway": "sway",
    "Hyprland": "hyprland",
    "hyprland": "hyprland",
    "weston": "weston",
    "wayfire": "wayfire",
    "labwc": "labwc",
    "cage": "cage",
    "river": "river",
}

_DESKTOP_COMPOSITORS = {
    "gnome": "mutter",
    "kde": "kwin",
    "plasma": "kwin",
}


def _normalize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    value = value.strip()
    return value or None


def _get_first_env(*names: str) -> Optional[str]:
    for name in names:
        value = _normalize(os.environ.get(name))
        if value is not None:
            return value

    return None


def _get_running_compositor() -> Optional[str]:
    try:
        result = subprocess.run(
            ["ps", "-eo", "comm="],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    processes = {_normalize(process) for process in result.stdout.splitlines()}
    processes.discard(None)

    for process_name, compositor in _COMPOSITOR_PROCESSES.items():
        if process_name in processes:
            return compositor

    return None


def _get_compositor_from_desktop_environment() -> Optional[str]:
    desktop_environment = SystemInfo.get_desktop_environment()
    if desktop_environment is None:
        return None

    desktop_environment = desktop_environment.lower()
    for desktop_name, compositor in _DESKTOP_COMPOSITORS.items():
        if desktop_name in desktop_environment:
            return compositor

    return None


class SystemInfo:
    @staticmethod
    def get_os() -> Optional[str]:
        return _normalize(platform.system())

    @staticmethod
    def get_desktop_environment() -> Optional[str]:
        return _get_first_env(
            "XDG_CURRENT_DESKTOP",
            "DESKTOP_SESSION",
            "GDMSESSION",
        )

    @staticmethod
    def get_compositor() -> Optional[str]:
        return _get_running_compositor() or _get_compositor_from_desktop_environment()


def get_os() -> Optional[str]:
    return SystemInfo.get_os()


def get_desktop_environment() -> Optional[str]:
    return SystemInfo.get_desktop_environment()


def get_compositor() -> Optional[str]:
    return SystemInfo.get_compositor()
