"""Settings and preset presentation, separate from window lifecycle."""

import logging
from pathlib import Path

from PySide6.QtCore import QRect, QSignalBlocker
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMessageBox, QWidget

from usta.application.settings import AppSettings, Preset
from usta.config import (
    CONFIG_DIR,
    DPI_SCALE_DEFAULT,
    SETTINGS_TOPMOST_HOTKEY,
    TEMPORARY_REGION_HOTKEY,
)
from usta.i18n import _
from usta.infrastructure.settings_store import SettingsStore

logger = logging.getLogger(__name__)


class SettingsPresenter:
    def __init__(self, view, store=None):
        self.view = view
        self._loaded_settings = AppSettings()
        self.store = store if store is not None else SettingsStore(Path(CONFIG_DIR))

    def save_settings(self):
        if self.view._loading_settings:
            return
        settings = {
            "ocr_engine": self.view.ocr_tab.combo_ocr.currentText(),
            "translator_engine": self.view.translation_tab.combo_translator.currentText(),
            "source_lang": self.view.translation_tab.combo_source.currentText(),
            "target_lang": self.view.translation_tab.combo_target.currentText(),
            "font_family": self.view.appearance_tab.font_picker.currentFont().family(),
            "font_size": self.view.appearance_tab.font_size_spin.value(),
            "font_color": self.view.overlay.font_color,
            "bg_color": self.view.overlay.bg_color,
            "bg_opacity": self.view.overlay.bg_opacity,
            "translator_api_keys": self.view.api_keys,
            "capture_rect": (
                self.view.controller.capture_rect.x(),
                self.view.controller.capture_rect.y(),
                self.view.controller.capture_rect.width(),
                self.view.controller.capture_rect.height(),
            ),
            "dpi_scale": self.view.controller.dpi_scale,
            "screenshot_engine": self.view.ocr_tab.combo_screenshot.currentText(),
            "settings_topmost_hotkey": self.view.settings_topmost_hotkey,
            "temporary_region_hotkey": self.view.temporary_region_hotkey,
        }
        try:
            updated = AppSettings.from_dict({**self._loaded_settings.to_dict(), **settings})
            self.store.save(updated)
            self._loaded_settings = updated
            logger.info("Settings saved.")
        except Exception as e:
            logger.error(f"Settings save error: {e}")

    def load_settings(self):
        self.view._loading_settings = True
        blockers = [QSignalBlocker(widget) for widget in self.view.findChildren(QWidget)]
        try:
            self._loaded_settings = self.store.load()
            s = self._loaded_settings.to_dict()
            # Apply UI values while signals and persistence are blocked.
            self.view.ocr_tab.combo_ocr.setCurrentText(s.get("ocr_engine", "Tesseract"))
            self.view.translation_tab.combo_translator.setCurrentText(
                s.get("translator_engine", "Google")
            )
            self.view.translation_tab.combo_source.setCurrentText(s.get("source_lang", "English"))
            self.view.translation_tab.combo_target.setCurrentText(s.get("target_lang", "Turkish"))

            font_family = s.get("font_family", "Arial")
            self.view.appearance_tab.font_picker.setCurrentFont(QFont(font_family))
            self.view.overlay.set_font_family(font_family)

            font_size = s.get("font_size", 20)
            self.view.appearance_tab.font_size_spin.setValue(font_size)
            self.view.overlay.set_font_size(font_size)

            font_color = s.get("font_color", "white")
            self.view.overlay.set_font_color(font_color)
            self.view.appearance_tab.color_sample.setStyleSheet(
                f"background-color: {font_color}; border: 1px solid gray; border-radius: 4px;"
            )

            bg_color = s.get("bg_color", "#000000")
            self.view.overlay.set_bg_color(bg_color)
            self.view.appearance_tab.bg_color_sample.setStyleSheet(
                f"background-color: {bg_color}; border: 1px solid gray; border-radius: 4px;"
            )

            bg_opacity = s.get("bg_opacity", 180)
            self.view.appearance_tab.bg_opacity_spin.setValue(bg_opacity)
            self.view.overlay.set_bg_opacity(bg_opacity)

            # Load DPI scale
            dpi_scale = s.get("dpi_scale", DPI_SCALE_DEFAULT)

            self.view.ocr_tab.dpi_scale_spin.setValue(dpi_scale * 100)

            self.view.controller.dpi_scale = dpi_scale
            self.view.region_controller.main_dpi_scale = self.view.controller.dpi_scale

            rect = s.get("capture_rect")
            if rect:
                self.view.controller.set_rect(QRect(rect[0], rect[1], rect[2], rect[3]))
                self.view.region_controller.main_capture_rect = QRect(
                    self.view.controller.capture_rect
                )
                self.view.update_rect_label()

            # Load screenshot engine
            screenshot_engine = s.get("screenshot_engine", "Portal")
            self.view.ocr_tab.combo_screenshot.setCurrentText(screenshot_engine)
            self.view.controller.set_screenshot_engine(screenshot_engine)

            # Load API keys
            self.view.api_keys = s.get("translator_api_keys", {})
            self._apply_api_key_for_current_engine()

            self.view._apply_saved_hotkeys(
                s.get("settings_topmost_hotkey", SETTINGS_TOPMOST_HOTKEY),
                s.get("temporary_region_hotkey", TEMPORARY_REGION_HOTKEY),
            )

            self.view.controller.set_engine(self.view.ocr_tab.combo_ocr.currentText())
            self.view.controller.set_translator(
                self.view.translation_tab.combo_translator.currentText()
            )
            self.view.update_languages()
        except (OSError, ValueError) as exc:
            logger.error(f"Settings load error: {exc}")
            self.view._apply_saved_hotkeys(SETTINGS_TOPMOST_HOTKEY, TEMPORARY_REGION_HOTKEY)
            self.view.update_languages()
        finally:
            del blockers
            self.view._loading_settings = False

    def _apply_api_key_for_current_engine(self):
        """Update the API key textbox state and value for the current engine."""
        engine = self.view.translation_tab.combo_translator.currentText()
        key = self.view.api_keys.get(engine, "")
        # Block signals to avoid triggering on_api_key_changed during load
        self.view.translation_tab.api_key_input.blockSignals(True)
        self.view.translation_tab.api_key_input.setText(key)
        self.view.translation_tab.api_key_input.blockSignals(False)
        # Push to worker so the engine uses the saved key
        if key:
            self.view.controller.set_api_key(engine, key)
        # Toggle editable state based on engine (always visible, fixed window size)
        self._update_api_key_state(engine)

    def _update_api_key_state(self, engine: str):
        """Enable/disable the API key field based on engine, keep it always visible."""
        engines_needing_key = {"DeepL"}
        if engine in engines_needing_key:
            self.view.translation_tab.api_key_input.setReadOnly(False)
            self.view.translation_tab.api_key_input.setEnabled(True)
            self.view.translation_tab.api_key_input.setToolTip("")
        else:
            self.view.translation_tab.api_key_input.setReadOnly(True)
            self.view.translation_tab.api_key_input.setEnabled(False)
            self.view.translation_tab.api_key_input.setToolTip(
                _("This engine does not require an API key")
            )

    def on_translator_changed(self, engine: str):
        """Called when the translation engine combo box changes."""
        self._apply_api_key_for_current_engine()

    def on_api_key_changed(self, text: str):
        """Called when the user types in the API key text box."""
        engine = self.view.translation_tab.combo_translator.currentText()
        self.view.api_keys[engine] = text
        self.view.controller.set_api_key(engine, text)
        self.save_settings()

    def _load_presets_dict(self):
        try:
            return {name: preset.to_dict() for name, preset in self.store.load_presets().items()}
        except (OSError, ValueError) as exc:
            logger.error(f"Presets load error: {exc}")
            return {}

    def _save_presets_dict(self, presets):
        try:
            self.store.save_presets(
                {name: Preset.from_dict(value) for name, value in presets.items()}
            )
            return True
        except (OSError, ValueError) as exc:
            logger.error(f"Presets save error: {exc}")
            return False

    def refresh_preset_list(self):
        """Refresh the combo box with preset names."""
        self.view.save_tab.preset_combo.clear()
        presets = self._load_presets_dict()
        for name in sorted(presets.keys()):
            self.view.save_tab.preset_combo.addItem(name)

    def save_preset(self):
        """Save current overlay position/size + capture rect + appearance to a named preset."""
        name = self.view.save_tab.preset_name_input.text().strip()
        if not name:
            QMessageBox.warning(self.view, _("No Name"), _("Please enter a preset name."))
            return

        preset = {
            "capture_rect": (
                self.view.controller.capture_rect.x(),
                self.view.controller.capture_rect.y(),
                self.view.controller.capture_rect.width(),
                self.view.controller.capture_rect.height(),
            ),
            "overlay_x": self.view.overlay.pos().x(),
            "overlay_y": self.view.overlay.pos().y(),
            "overlay_w": self.view.overlay.width(),
            "overlay_h": self.view.overlay.height(),
            "font_family": self.view.overlay.font_family,
            "font_size": self.view.overlay.font_size,
            "font_color": self.view.overlay.font_color,
            "bg_color": self.view.overlay.bg_color,
            "bg_opacity": self.view.overlay.bg_opacity,
        }

        presets = self._load_presets_dict()
        presets[name] = preset
        if not self._save_presets_dict(presets):
            return
        self.refresh_preset_list()
        self.view.save_tab.preset_name_input.clear()
        logger.info(f"Preset '{name}' saved.")

    def load_preset(self):
        """Load the selected preset from the combo box and apply it."""
        name = self.view.save_tab.preset_combo.currentText()
        if not name:
            QMessageBox.information(
                self.view, _("No Selection"), _("Please select a preset to load.")
            )
            return
        presets = self._load_presets_dict()
        preset = presets.get(name)
        if preset is None:
            QMessageBox.warning(
                self.view, _("Not Found"), _("Preset '{name}' not found.").format(name=name)
            )
            return

        # Apply capture rect
        rect_data = preset.get("capture_rect")
        if rect_data:
            self.view.region_controller.apply_main_region(QRect(*rect_data))
            self.view.update_rect_label()

        # Apply overlay position and size
        ox = preset.get("overlay_x")
        oy = preset.get("overlay_y")
        ow = preset.get("overlay_w")
        oh = preset.get("overlay_h")
        if ox is not None and oy is not None:
            self.view.overlay.move(ox, oy)
        if ow is not None and oh is not None:
            self.view.overlay.resize(ow, oh)

        # Apply appearance
        ff = preset.get("font_family")
        if ff:
            self.view.overlay.set_font_family(ff)
            self.view.appearance_tab.font_picker.setCurrentFont(QFont(ff))

        fs = preset.get("font_size")
        if fs:
            self.view.overlay.set_font_size(fs)
            self.view.appearance_tab.font_size_spin.setValue(fs)

        fc = preset.get("font_color")
        if fc:
            self.view.overlay.set_font_color(fc)
            self.view.appearance_tab.color_sample.setStyleSheet(
                f"background-color: {fc}; border: 1px solid gray; border-radius: 4px;"
            )

        bgc = preset.get("bg_color")
        if bgc:
            self.view.overlay.set_bg_color(bgc)
            self.view.appearance_tab.bg_color_sample.setStyleSheet(
                f"background-color: {bgc}; border: 1px solid gray; border-radius: 4px;"
            )

        bgo = preset.get("bg_opacity")
        if bgo is not None:
            self.view.overlay.set_bg_opacity(bgo)
            self.view.appearance_tab.bg_opacity_spin.setValue(bgo)

        logger.info(f"Preset '{name}' loaded.")

    def delete_preset(self):
        """Delete the selected preset."""
        name = self.view.save_tab.preset_combo.currentText()
        if not name:
            QMessageBox.information(
                self.view, _("No Selection"), _("Please select a preset to delete.")
            )
            return
        presets = self._load_presets_dict()
        if name in presets:
            del presets[name]
            if not self._save_presets_dict(presets):
                return
            self.refresh_preset_list()
            logger.info(f"Preset '{name}' deleted.")
        else:
            QMessageBox.warning(
                self.view, _("Not Found"), _("Preset '{name}' not found.").format(name=name)
            )
