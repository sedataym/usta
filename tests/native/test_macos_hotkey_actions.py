import json
import gc
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import threading
import unittest
import weakref
from unittest import mock

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, Qt, QPoint, QRect
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

from usta.core.sniper.core_sniper import CoreSniper, OverlayWindow, SelectionManager
from usta.ui.macos_hotkeys import MacOSHotkeyWindow


def pump(milliseconds=40):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


@unittest.skipUnless(os.environ.get('USTA_NATIVE_TESTS') == '1' and sys.platform == 'darwin', 'Requires macOS')
class MacOSHotkeyActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import AppKit
        import objc
        cls.cocoa = AppKit
        cls.objc = objc
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def make_control_panel(self, os_name):
        from contextlib import ExitStack
        from usta.ui.main_window import ControlPanel

        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch('usta.ui.main_window.OS', os_name))
        stack.enter_context(mock.patch('usta.ui.overlay_window.OS', os_name))
        stack.enter_context(mock.patch('usta.core.shortcut.GlobalHotkey.start', return_value=False))
        stack.enter_context(mock.patch.object(ControlPanel, 'load_settings'))
        stack.enter_context(mock.patch.object(ControlPanel, 'save_settings'))
        stack.enter_context(mock.patch.object(ControlPanel, 'refresh_preset_list'))
        quit_app = stack.enter_context(mock.patch.object(QApplication, 'quit'))
        worker = stack.enter_context(mock.patch('usta.ui.main_window.OCRWorker')).return_value
        worker.capture_rect = QRect(10, 20, 200, 50)
        worker.dpi_scale = 1.0
        worker.set_rect.side_effect = lambda rect: setattr(worker, 'capture_rect', QRect(rect))
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
        panel, quit_app = self.make_control_panel('Linux')
        self.assertIsNone(panel._macos_hotkey_window)
        self.assertIsNone(panel.overlay._macos_rules)
        with mock.patch.object(panel, 'raise_') as raise_window, \
             mock.patch.object(panel, 'activateWindow') as activate:
            panel.set_settings_always_on_top(True)
            self.assertTrue(panel.windowFlags() & Qt.WindowStaysOnTopHint)
            raise_window.assert_called_once()
            activate.assert_called_once()
        panel.set_settings_always_on_top(False)
        self.assertFalse(panel.windowFlags() & Qt.WindowStaysOnTopHint)
        panel.close()
        quit_app.assert_not_called()

    def test_linux_region_selector_keeps_x11_flags_without_native_imports(self):
        with mock.patch('usta.core.sniper.core_sniper.sys.platform', 'linux'), \
             mock.patch.dict(sys.modules, {'usta.ui.macos_hotkeys': None}):
            manager = SelectionManager()
            window = OverlayWindow(self.app.primaryScreen(), manager)
            self.assertTrue(window.windowFlags() & Qt.X11BypassWindowManagerHint)
            self.assertIsNone(window._macos_hotkey_window)
            window.deleteLater()
            pump()

    def test_region_windows_are_destroyed_on_gui_thread_before_worker_collection(self):
        import shiboken6

        for cancel in (False, True):
            with self.subTest(cancel=cancel):
                windows = []
                destroyed_on = []
                gui_thread = threading.get_ident()

                def finish():
                    windows.extend(w for w in self.app.topLevelWidgets()
                                   if isinstance(w, OverlayWindow) and w.isVisible())
                    for window in windows:
                        window.destroyed.connect(
                            lambda: destroyed_on.append(threading.get_ident()),
                            Qt.DirectConnection,
                        )
                    windows[0].manager.selectionFinished.emit(
                        QRect() if cancel else QRect(50, 50, 150, 50))

                QTimer.singleShot(100, finish)
                rect = CoreSniper().get_region()
                self.assertEqual(rect, None if cancel else QRect(50, 50, 150, 50))
                # close() only hides QWidget. Native resources must also be
                # deleted even while Python references/cycles still exist.
                QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
                try:
                    self.assertTrue(windows)
                    self.assertTrue(all(not shiboken6.isValid(w) for w in windows),
                                    'Closed selection windows retain live native widgets')
                    self.assertEqual(destroyed_on, [gui_thread] * len(windows))
                    windows.clear()
                    worker = threading.Thread(target=gc.collect)
                    worker.start()
                    worker.join(timeout=5)
                    self.assertFalse(worker.is_alive())
                    pump()
                finally:
                    for window in windows:
                        if shiboken6.isValid(window):
                            window.deleteLater()
                    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_worker_collection_cannot_destroy_pending_region_windows(self):
        import shiboken6

        references = []
        destroyed_on = []
        gui_thread = threading.get_ident()

        def finish():
            for window in self.app.topLevelWidgets():
                if isinstance(window, OverlayWindow) and window.isVisible():
                    references.append(weakref.ref(window))
                    window.destroyed.connect(
                        lambda: destroyed_on.append(threading.get_ident()),
                        Qt.DirectConnection,
                    )
                    window.manager.selectionFinished.emit(QRect(50, 50, 150, 50))

        was_enabled = gc.isenabled()
        gc.disable()
        try:
            QTimer.singleShot(100, finish)
            self.assertEqual(CoreSniper().get_region(), QRect(50, 50, 150, 50))
            # Simulate OCR startup collecting Python cycles immediately, before
            # the GUI has even had time to process its deferred-delete events.
            worker = threading.Thread(target=gc.collect)
            worker.start()
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
            self.assertEqual(destroyed_on, [])
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            self.assertTrue(references)
            self.assertEqual(destroyed_on, [gui_thread] * len(references))
            self.assertTrue(all(ref() is None or not shiboken6.isValid(ref())
                                for ref in references))
            pump()
        finally:
            if was_enabled:
                gc.enable()

    def test_macos_controls_use_native_action_and_restore_temporary_region(self):
        panel, quit_app = self.make_control_panel('Darwin')
        self.assertEqual(panel.windowType(), Qt.Tool)
        with mock.patch.object(panel._macos_hotkey_window, 'show') as show, \
             mock.patch.object(panel._macos_hotkey_window, 'lower') as lower, \
             mock.patch.object(panel, 'raise_') as raise_window, \
             mock.patch.object(panel, 'activateWindow') as activate:
            panel.overlay._toggle_main_window_topmost()
            show.assert_called_once()
            panel.overlay._toggle_main_window_topmost()
            lower.assert_called_once()
            raise_window.assert_not_called()
            activate.assert_not_called()
        original = QRect(panel.worker.capture_rect)
        panel._apply_temporary_region(QRect(100, 100, 300, 80), 2.0)
        panel._apply_temporary_region(QRect(200, 200, 300, 80), 1.5)
        self.assertGreater(panel._temporary_region_restore_timer.remainingTime(), 9000)
        panel._temporary_region_restore_timer.timeout.emit()
        self.assertEqual(panel.worker.capture_rect, original)
        self.assertEqual(panel.worker.dpi_scale, 1.0)
        self.assertFalse(panel._temporary_region_active)
        with mock.patch.object(panel, '_get_selected_region_and_dpi', return_value=(None, None)):
            panel.select_temporary_region()
        self.assertEqual(panel.worker.capture_rect, original)
        self.assertFalse(panel._temporary_region_selecting)
        panel.close()
        quit_app.assert_called_once()

    def test_settings_and_region_selection_preserve_fullscreen_space(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'state'
            exit_file = Path(directory) / 'exit'
            helper = Path(__file__).parent / 'helpers' / 'macos_fullscreen_host.py'
            process = subprocess.Popen([sys.executable, str(helper), str(state), str(exit_file)])
            panel = QWidget()
            panel.setWindowFlags(Qt.Tool | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
            panel.setAttribute(Qt.WA_ShowWithoutActivating)
            panel.setAttribute(Qt.WA_MacAlwaysShowToolWindow)
            panel.setGeometry(180, 180, 320, 180)
            actions = MacOSHotkeyWindow(panel)
            try:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    pump()
                    if state.exists():
                        try:
                            if json.loads(state.read_text())['fullscreen']:
                                break
                        except json.JSONDecodeError:
                            pass
                else:
                    self.fail('Fullscreen host did not enter its Space')
                actions.show()
                pump(450)
                native = self.objc.objc_object(c_void_p=int(panel.winId())).window()
                self.assertTrue(native.isOnActiveSpace())
                self.assertTrue(native.isKindOfClass_(self.cocoa.NSPanel))
                self.assertTrue(native.styleMask() & self.cocoa.NSWindowStyleMaskTitled)
                import Quartz
                on_screen = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, 0)
                self.assertTrue(any(w['kCGWindowOwnerPID'] == process.pid for w in on_screen),
                                'Showing settings switched away from the fullscreen Space')
                # A panel can become key while its owning app remains inactive.
                self.assertIn(self.cocoa.NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier(),
                              (os.getpid(), process.pid))
                self.assertTrue(native.isKeyWindow())
                actions.lower()
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    pump()
                    if self.cocoa.NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier() == process.pid:
                        break
                self.assertEqual(native.level(), self.cocoa.NSNormalWindowLevel)
                self.assertEqual(self.cocoa.NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier(), process.pid)
                observations = []
                def select():
                    windows = [w for w in self.app.topLevelWidgets()
                               if isinstance(w, OverlayWindow) and w.isVisible()]
                    if not windows:
                        observations.append(False)
                        return
                    target = next((w for w in windows if w.screen_geometry.contains(QPoint(150, 150))), windows[0])
                    n = self.objc.objc_object(c_void_p=int(target.winId())).window()
                    observations.append(n.isOnActiveSpace())
                    on_screen = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, 0)
                    observations.append(any(w['kCGWindowOwnerPID'] == process.pid for w in on_screen))
                    QTest.mousePress(target, Qt.LeftButton, pos=QPoint(50, 50))
                    QTest.mouseMove(target, QPoint(200, 100))
                    QTest.mouseRelease(target, Qt.LeftButton, pos=QPoint(200, 100))
                QTimer.singleShot(150, select)
                # A watchdog avoids a stuck nested loop on failure.
                watchdog = QTimer()
                watchdog.setSingleShot(True)
                watchdog.timeout.connect(lambda: [w.manager.selectionFinished.emit(QRect())
                                                   for w in self.app.topLevelWidgets()
                                                   if isinstance(w, OverlayWindow) and w.isVisible()])
                watchdog.start(1500)
                try:
                    rect = CoreSniper().get_region()
                finally:
                    watchdog.stop()
                self.assertIsNotNone(rect)
                self.assertEqual(observations, [True, True])
                self.assertEqual(rect.size().width(), 151)
                self.assertEqual(rect.size().height(), 51)
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    pump()
                    if self.cocoa.NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier() == process.pid:
                        break
                self.assertEqual(self.cocoa.NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier(), process.pid)
                def cancel():
                    for window in self.app.topLevelWidgets():
                        if isinstance(window, OverlayWindow) and window.isVisible():
                            QTest.keyClick(window, Qt.Key_Escape)
                            break
                QTimer.singleShot(150, cancel)
                watchdog.start(1500)
                try:
                    self.assertIsNone(CoreSniper().get_region())
                finally:
                    watchdog.stop()
                self.assertFalse(any(isinstance(w, OverlayWindow) and w.isVisible()
                                     for w in self.app.topLevelWidgets()))
            finally:
                actions.stop()
                panel.close()
                panel.deleteLater()
                process.terminate()
                process.wait(timeout=5)
                pump()
