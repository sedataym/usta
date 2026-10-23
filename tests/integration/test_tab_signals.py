"""Qt forwards widget signals without leaking arguments into no-argument signals."""

import unittest
from unittest.mock import patch

from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QPushButton

from usta.i18n import _
from usta.ui.tabs import AppearanceTab, HotkeyTab, OCRTab, SaveTab, TranslationTab


class TabSignalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ocr_and_capture_selections_emit_value_and_one_change(self):
        tab = OCRTab()
        self.addCleanup(tab.close)
        for combo, forwarded in (
            (tab.combo_ocr, tab.engine_changed),
            (tab.combo_screenshot, tab.screen_engine_changed),
        ):
            if combo.count() < 2:
                combo.addItem("Other capture backend")
            changed, value = QSignalSpy(tab.changed), QSignalSpy(forwarded)
            with patch("sys.excepthook") as unhandled:
                combo.setCurrentIndex((combo.currentIndex() + 1) % combo.count())
                self.app.processEvents()
            unhandled.assert_not_called()
            self.assertEqual(changed.count(), 1)
            self.assertEqual(value.count(), 1)
            self.assertEqual(value.at(0), [combo.currentText()])

    def test_source_target_and_provider_selections_forward_without_typeerror(self):
        tab = TranslationTab()
        self.addCleanup(tab.close)
        for combo in (tab.combo_source, tab.combo_target):
            changed = QSignalSpy(tab.language_changed)
            with patch("sys.excepthook") as unhandled:
                combo.setCurrentIndex((combo.currentIndex() + 1) % combo.count())
                self.app.processEvents()
            unhandled.assert_not_called()
            self.assertEqual(changed.count(), 1)
        changed = QSignalSpy(tab.changed)
        selected = QSignalSpy(tab.translator_selected)
        with patch("sys.excepthook") as unhandled:
            tab.combo_translator.setCurrentText("DeepL")
            self.app.processEvents()
        unhandled.assert_not_called()
        self.assertEqual(changed.count(), 1)
        self.assertEqual(selected.at(0), ["DeepL"])

    def test_action_buttons_drop_clicked_boolean(self):
        save, appearance, hotkeys = SaveTab(), AppearanceTab(), HotkeyTab()
        for tab in (save, appearance, hotkeys):
            self.addCleanup(tab.close)
        resets = [b for b in hotkeys.findChildren(QPushButton) if b.text() == _("Reset")]
        cases = [
            (save.btn_save_preset, save.save_requested),
            (save.btn_load_preset, save.load_requested),
            (save.btn_delete_preset, save.delete_requested),
            (appearance.btn_color, appearance.text_color_requested),
            (appearance.btn_bg_color, appearance.background_color_requested),
            (resets[0], hotkeys.reset_settings_requested),
            (resets[1], hotkeys.reset_region_requested),
        ]
        for button, signal in cases:
            with self.subTest(button=button.text()):
                requested = QSignalSpy(signal)
                with patch("sys.excepthook") as unhandled:
                    button.click()
                    self.app.processEvents()
                unhandled.assert_not_called()
                self.assertEqual(requested.count(), 1)
