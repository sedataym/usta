import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QColorDialog, QSystemTrayIcon

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
        self.addCleanup(lambda: self.panel.request_quit())

    def test_tray_shortcut_and_x_share_real_visibility(self):
        panel = self.panel
        with mock.patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=True):
            panel.overlay.show()
            panel.overlay.settings_topmost_hotkey_pressed.emit()
            self.assertFalse(panel.isVisible())
            self.assertTrue(panel.overlay.isVisible())
            panel.tray.main_action.trigger()
            self.assertTrue(panel.isVisible())
            self.assertTrue(panel.windowFlags() & Qt.WindowStaysOnTopHint)
            panel.close()
            self.assertFalse(panel.isVisible())
            self.assertTrue(panel.overlay.isVisible())
            self.assertFalse(panel._closing)
            panel.overlay._rearm_settings_topmost_hotkey()
            panel.overlay.settings_topmost_hotkey_pressed.emit()
            self.assertTrue(panel.isVisible())
            panel.tray.refresh()
            self.assertEqual(panel.tray.main_action.text(), "Hide Main Window")

    def test_delayed_startup_alignment_does_not_reveal_hidden_overlay(self):
        self.panel.overlay.hide()
        self.panel.align_overlay()
        self.assertFalse(self.panel.overlay.isVisible())

    def test_minimized_main_window_is_restored_by_toggle(self):
        self.panel.showMinimized()
        self.panel.toggle_main_window()
        self.assertTrue(self.panel.isVisible())
        self.assertFalse(self.panel.isMinimized())
        self.assertTrue(self.panel.windowFlags() & Qt.WindowStaysOnTopHint)

    def test_overlay_stays_hidden_when_new_translation_arrives(self):
        panel = self.panel
        panel.overlay.show()
        panel.tray.overlay_action.trigger()
        panel.overlay.update_text("still translating")
        self.assertFalse(panel.overlay.isVisible())
        self.assertTrue(panel.isVisible())
        self.assertEqual(panel.overlay.label.text(), "still translating")
        panel.tray.refresh()
        self.assertEqual(panel.tray.overlay_action.text(), "Show Overlay")
        panel.tray.overlay_action.trigger()
        self.assertTrue(panel.overlay.isVisible())
        self.assertTrue(panel.overlay.windowFlags() & Qt.WindowStaysOnTopHint)

    def test_tray_start_stop_follow_worker_state_and_disable_during_quit(self):
        panel = self.panel
        panel.tray.refresh()
        self.assertTrue(panel.tray.start_action.isEnabled())
        self.assertFalse(panel.tray.stop_action.isEnabled())
        with mock.patch.object(panel.worker, "isRunning", return_value=True):
            panel.tray.refresh()
            self.assertFalse(panel.tray.start_action.isEnabled())
            self.assertTrue(panel.tray.stop_action.isEnabled())
            panel._closing = True
            panel.tray.refresh()
            self.assertFalse(panel.tray.start_action.isEnabled())
            self.assertFalse(panel.tray.stop_action.isEnabled())

    def test_tray_temporary_region_requires_running_worker(self):
        panel = self.panel
        panel.tray.refresh()
        self.assertFalse(panel.tray.temporary_region_action.isEnabled())
        with mock.patch.object(panel.worker, "isRunning", return_value=True):
            panel.tray.refresh()
            self.assertTrue(panel.tray.temporary_region_action.isEnabled())
            panel._temporary_region_selecting = True
            panel.tray.refresh()
            self.assertFalse(panel.tray.temporary_region_action.isEnabled())

    def test_stopping_before_delayed_temporary_selection_does_not_open_selector(self):
        panel = self.panel
        with (
            mock.patch.object(panel.worker, "isRunning", return_value=True) as running,
            mock.patch.object(
                panel, "_get_selected_region_and_dpi", return_value=(QRect(1, 2, 100, 50), None)
            ) as select,
        ):
            panel.tray.refresh()
            panel.tray.temporary_region_action.trigger()
            running.return_value = False
            QTest.qWait(250)
            select.assert_not_called()
            self.assertFalse(panel.region_controller.temporary_active)

    def test_quit_waits_for_worker_then_cleans_up_hidden_windows(self):
        panel = self.panel
        panel.overlay.show()
        panel.hide()
        with (
            mock.patch.object(panel.worker, "isRunning", return_value=True),
            mock.patch.object(panel.controller, "stop") as stop,
            mock.patch.object(panel.worker, "close") as close_worker,
            mock.patch.object(QApplication, "quit") as quit_app,
        ):
            panel.tray.quit_action.trigger()
            self.assertTrue(panel._closing)
            stop.assert_called_once()
            close_worker.assert_not_called()
            quit_app.assert_not_called()
            # A second quit request must not register another finished handler.
            panel.request_quit()
            stop.assert_called_once()
        with (
            mock.patch.object(panel.worker, "isRunning", return_value=False),
            mock.patch.object(QApplication, "quit") as quit_app,
        ):
            panel.worker.finished.emit()
            self.assertFalse(panel.overlay.isVisible())
            self.assertFalse(panel.tray.icon.isVisible())
            quit_app.assert_called_once()

    def test_x_exits_when_system_tray_is_unavailable(self):
        panel = self.panel
        panel.overlay.show()
        with (
            mock.patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=False),
            mock.patch.object(QApplication, "quit") as quit_app,
        ):
            panel.close()
            self.assertFalse(panel.overlay.isVisible())
            quit_app.assert_called_once()

    def test_load_does_not_write_and_user_change_writes_once(self):
        self.save_spy.assert_not_called()
        self.assertEqual(self.panel.appearance_tab.font_size_spin.value(), 27)
        self.assertEqual(self.panel.translation_tab.combo_target.currentText(), "German")
        self.panel.appearance_tab.font_size_spin.setValue(28)
        self.save_spy.assert_called_once()
        self.assertEqual(self.store.load().translator_api_keys, {"DeepL": "secret"})

    def test_color_dialog_accept_and_cancel_keep_tool_panel_alive(self):
        # macOS uses a Tool panel, which does not count towards Qt's last window.
        self.panel.setWindowFlag(Qt.Tool, True)
        self.panel.show()
        self.app.processEvents()
        for button, field, sample in (
            (
                self.panel.appearance_tab.btn_color,
                "font_color",
                self.panel.appearance_tab.color_sample,
            ),
            (
                self.panel.appearance_tab.btn_bg_color,
                "bg_color",
                self.panel.appearance_tab.bg_color_sample,
            ),
        ):
            for accept in (True, False):
                with self.subTest(field=field, accept=accept):
                    before = getattr(self.store.load(), field)
                    last_closed = QSignalSpy(self.app.lastWindowClosed)
                    self.save_spy.reset_mock()

                    def finish_dialog():
                        dialog = next(
                            w
                            for w in self.app.topLevelWidgets()
                            if isinstance(w, QColorDialog) and w.isVisible()
                        )
                        dialog.setCurrentColor(QColor("#123456" if accept else "#abcdef"))
                        if accept:
                            dialog.accept()
                        else:
                            dialog.reject()

                    def choose():
                        QTimer.singleShot(0, finish_dialog)
                        button.click()

                    QTimer.singleShot(0, choose)
                    exit_timer = QTimer()
                    exit_timer.setSingleShot(True)
                    exit_timer.timeout.connect(lambda: self.app.exit(0))
                    exit_timer.start(50)
                    self.app.exec()
                    exit_timer.stop()
                    self.assertEqual(last_closed.count(), 0)
                    self.assertTrue(self.panel.isVisible())
                    expected = "#123456" if accept else before
                    self.assertEqual(getattr(self.panel.overlay, field), expected)
                    self.assertEqual(getattr(self.store.load(), field), expected)
                    self.assertIn(expected, sample.styleSheet())
                    self.assertEqual(self.save_spy.call_count, 1 if accept else 0)

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

    def test_status_does_not_increase_main_window_height(self):
        panel = self.panel
        other_tab_height = max(
            panel.tabs.widget(index).minimumSizeHint().height()
            for index in range(panel.tabs.count())
            if panel.tabs.widget(index) is not panel.status_tab
        )
        self.assertLessEqual(panel.status_tab.minimumSizeHint().height(), other_tab_height)

    def test_region_status_displays_coordinates_and_dimensions_separately(self):
        from PySide6.QtGui import QFontInfo

        tab = self.panel.status_tab
        self.panel._apply_main_region(QRect(-1920, 120, 1280, 720))
        self.assertEqual(tab.region_position.text(), "X -1920   Y 120")
        self.assertEqual(tab.region_size.text(), "1280 × 720 px")
        for label in (tab.region_position, tab.region_size):
            self.assertTrue(QFontInfo(label.font()).fixedPitch())

    def test_stage_timings_update_individual_digital_displays_and_reset(self):
        from usta.application.results import PerformanceTimings

        tab = self.panel.status_tab
        self.panel.worker.timings_update.emit(PerformanceTimings(0.32, 1.28, 1.82))
        self.assertAlmostEqual(tab.ocr_value.value(), 0.32)
        self.assertAlmostEqual(tab.translation_value.value(), 1.28)
        self.assertAlmostEqual(tab.total_value.value(), 1.82)
        self.panel.update_system_status(False)
        for display in (tab.ocr_value, tab.translation_value, tab.total_value):
            self.assertEqual(display.value(), 0)
            self.assertIn("—", display.accessibleDescription())

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
