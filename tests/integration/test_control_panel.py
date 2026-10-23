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
