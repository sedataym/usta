import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication

from usta.application.settings import AppSettings, Preset
from usta.infrastructure.settings_store import SettingsStore


class ControlPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from usta.ui.main_window import ControlPanel

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = SettingsStore(Path(self.tmp.name))
        self.store.save(
            AppSettings(font_size=27, target_lang="German", translator_api_keys={"DeepL": "secret"})
        )
        self.stack = __import__("contextlib").ExitStack()
        self.addCleanup(self.stack.close)
        for name in ["usta.ui.main_window.OS", "usta.ui.overlay_window.OS"]:
            self.stack.enter_context(mock.patch(name, "Linux"))
        self.stack.enter_context(
            mock.patch("usta.core.shortcut.GlobalHotkey.start", return_value=False)
        )
        self.stack.enter_context(
            mock.patch("usta.ui.settings_presenter.SettingsStore", return_value=self.store)
        )
        self.save_spy = self.stack.enter_context(
            mock.patch.object(self.store, "save", wraps=self.store.save)
        )
        self.panel = ControlPanel()
        self.addCleanup(self.panel.close)

    def test_load_does_not_write_and_user_change_writes_once(self):
        self.save_spy.assert_not_called()
        self.assertEqual(self.panel.appearance_tab.font_size_spin.value(), 27)
        self.assertEqual(self.panel.translation_tab.combo_target.currentText(), "German")
        self.panel.appearance_tab.font_size_spin.setValue(28)
        self.save_spy.assert_called_once()
        self.assertEqual(self.store.load().translator_api_keys, {"DeepL": "secret"})

    def test_preset_cancels_temporary_restore(self):
        panel = self.panel
        self.store.save_presets({"game": Preset(capture_rect=(-100, 30, 600, 80))})
        panel.refresh_preset_list()
        panel._apply_temporary_region(QRect(10, 10, 100, 30), 2.0)
        panel.settings_presenter.load_preset()
        panel.region_controller.restore_timer.timeout.emit()
        self.assertFalse(panel.region_controller.temporary_active)
        self.assertEqual(panel.worker.capture_rect, QRect(-100, 30, 600, 80))

    def test_ui_save_preserves_unknown_migrated_fields(self):
        settings = AppSettings.from_dict(
            {"unknown_valid_field": {"format": "keep"}, "font_size": 26}
        )
        self.store.save(settings)
        self.panel.load_settings()
        self.panel.appearance_tab.font_size_spin.setValue(29)
        self.assertEqual(self.store.load().to_dict()["unknown_valid_field"], {"format": "keep"})

    def test_presenter_cannot_erase_valid_presets_when_one_entry_is_bad(self):
        import json

        path = Path(self.tmp.name) / "presets.json"
        raw = json.dumps(
            {"schema_version": 1, "data": {"valuable": {"font_size": 31}, "broken": None}}
        )
        path.write_text(raw)
        self.panel.refresh_preset_list()
        self.assertIn(
            "valuable",
            [
                self.panel.save_tab.preset_combo.itemText(i)
                for i in range(self.panel.save_tab.preset_combo.count())
            ],
        )
        self.panel.save_tab.preset_name_input.setText("new")
        self.panel.settings_presenter.save_preset()
        self.assertEqual(path.read_text(), raw)

    def test_running_status_restores_overlay_mode_after_queued_restart(self):
        with mock.patch.object(self.panel.overlay, "set_mode") as mode:
            self.panel.update_system_status(False)
            self.panel.update_system_status(True)
            self.assertEqual(mode.call_args_list, [mock.call(False), mock.call(True)])

    def test_region_status_uses_available_system_fixed_font(self):
        from PySide6.QtGui import QFontDatabase

        label = self.panel.status_tab.rect_label_status
        fixed = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self.assertEqual(label.font().family(), fixed.family())
        self.assertNotIn("monospace", label.styleSheet().lower())

    def test_stage_timings_are_single_line_above_region(self):
        from types import SimpleNamespace

        tab = self.panel.status_tab
        self.panel.worker.timings_update.emit(
            SimpleNamespace(ocr_seconds=0.32, translation_seconds=1.28, total_seconds=1.82)
        )
        text = tab.timings_label.text()
        for value in ("0.32", "1.28", "1.82"):
            self.assertIn(value, text)
        self.assertNotIn("\n", text)
        self.assertFalse(tab.timings_label.wordWrap())
        self.assertLess(
            tab.layout().indexOf(tab.timings_label), tab.layout().indexOf(tab.rect_label_status)
        )
        self.panel.update_system_status(False)
        self.assertNotIn("1.82", tab.timings_label.text())

    def test_region_button_uses_selection_icon_instead_of_emoji(self):
        self.assertNotIn("🖼", self.panel.btn_reg.text())
        self.assertFalse(self.panel.btn_reg.icon().isNull())
        self.assertFalse(self.panel.btn_reg.icon().pixmap(20, 20).isNull())

    def test_source_language_selection_updates_worker_and_saves_once(self):
        self.save_spy.reset_mock()
        with mock.patch("sys.excepthook") as unhandled:
            self.panel.translation_tab.combo_source.setCurrentText("Spanish")
            self.app.processEvents()
        unhandled.assert_not_called()
        self.assertEqual(self.panel.worker.pipeline.settings.source_lang, "es")
        self.assertEqual(self.store.load().source_lang, "Spanish")
        self.save_spy.assert_called_once()

    def test_ocr_selection_updates_worker_and_persists(self):
        self.save_spy.reset_mock()
        with mock.patch("sys.excepthook") as unhandled:
            self.panel.ocr_tab.combo_ocr.setCurrentText("EasyOCR")
            self.app.processEvents()
        unhandled.assert_not_called()
        self.assertEqual(self.panel.worker.pipeline.settings.ocr_engine, "EasyOCR")
        self.assertEqual(self.store.load().ocr_engine, "EasyOCR")
        self.save_spy.assert_called_once()

    def test_target_and_provider_changes_update_worker_and_persist_once(self):
        tab = self.panel.translation_tab
        cases = (
            (tab.combo_target, "Japanese", "target_lang", "ja"),
            (tab.combo_translator, "DeepL", "translator_engine", "DeepL"),
        )
        for combo, selection, field, worker_value in cases:
            with self.subTest(field=field):
                self.save_spy.reset_mock()
                with mock.patch("sys.excepthook") as unhandled:
                    combo.setCurrentText(selection)
                    self.app.processEvents()
                unhandled.assert_not_called()
                self.assertEqual(getattr(self.panel.worker.pipeline.settings, field), worker_value)
                self.assertEqual(getattr(self.store.load(), field), selection)
                self.save_spy.assert_called_once()
