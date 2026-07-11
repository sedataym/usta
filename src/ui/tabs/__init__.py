"""Control panel tab builders."""

from src.ui.tabs.about_tab import build_about_tab
from src.ui.tabs.appearance_tab import build_appearance_tab
from src.ui.tabs.ocr_tab import build_ocr_tab
from src.ui.tabs.save_tab import build_save_tab
from src.ui.tabs.hotkey_tab import build_hotkey_tab
from src.ui.tabs.status_tab import build_status_tab
from src.ui.tabs.translation_tab import build_translation_tab

__all__ = [
    "build_about_tab",
    "build_appearance_tab",
    "build_ocr_tab",
    "build_save_tab",
    "build_hotkey_tab",
    "build_status_tab",
    "build_translation_tab",
]
