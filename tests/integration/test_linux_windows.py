import sys
import unittest
from unittest import mock

from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication

from tests.native.test_macos_hotkey_actions import pump
from usta.ui.region_selection.core_sniper import OverlayWindow, SelectionManager


class LinuxWindowContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def make_control_panel(self, os_name):
        from contextlib import ExitStack

        from usta.ui.main_window import ControlPanel

        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch("usta.ui.main_window.OS", os_name))
        stack.enter_context(mock.patch("usta.ui.overlay_window.OS", os_name))
        stack.enter_context(mock.patch("usta.core.shortcut.GlobalHotkey.start", return_value=False))
        stack.enter_context(mock.patch.object(ControlPanel, "load_settings"))
        stack.enter_context(mock.patch.object(ControlPanel, "save_settings"))
        stack.enter_context(mock.patch.object(ControlPanel, "refresh_preset_list"))
        quit_app = stack.enter_context(mock.patch.object(QApplication, "quit"))
        worker = stack.enter_context(mock.patch("usta.ui.main_window.OCRWorker")).return_value
        worker.isRunning.return_value = False
        worker.capture_rect = QRect(10, 20, 200, 50)
        worker.dpi_scale = 1.0
        worker.set_rect.side_effect = lambda rect: setattr(worker, "capture_rect", QRect(rect))
        panel = ControlPanel()
        pump(150)  # Finish the normal startup overlay-position timer.

        def close():
            if panel.isVisible():
                panel.close()
            panel.overlay.deleteLater()
            panel.deleteLater()
            pump()

        self.addCleanup(close)
        return panel, quit_app

    def test_linux_settings_action_keeps_original_window_behavior(self):
        panel, quit_app = self.make_control_panel("Linux")
        self.assertIsNone(panel._macos_hotkey_window)
        self.assertIsNone(panel.overlay._macos_rules)
        with (
            mock.patch.object(panel, "raise_") as raise_window,
            mock.patch.object(panel, "activateWindow") as activate,
        ):
            panel.set_settings_always_on_top(True)
            self.assertTrue(panel.windowFlags() & Qt.WindowStaysOnTopHint)
            raise_window.assert_called_once()
            activate.assert_called_once()
        panel.set_settings_always_on_top(False)
        self.assertFalse(panel.windowFlags() & Qt.WindowStaysOnTopHint)
        panel.close()
        quit_app.assert_not_called()

    def test_linux_region_selector_keeps_x11_flags_without_native_imports(self):
        with (
            mock.patch("usta.ui.region_selection.core_sniper.sys.platform", "linux"),
            mock.patch.dict(sys.modules, {"usta.ui.platform.macos.hotkeys": None}),
        ):
            manager = SelectionManager()
            window = OverlayWindow(self.app.primaryScreen(), manager)
            self.assertTrue(window.windowFlags() & Qt.X11BypassWindowManagerHint)
            self.assertIsNone(window._macos_hotkey_window)
            window.deleteLater()
            pump()
