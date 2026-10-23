import os
"""Native macOS integration tests; require a WindowServer session."""
import sys
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest import mock

from PySide6.QtCore import QEvent, QEventLoop, QTimer, Qt
from PySide6.QtWidgets import QApplication, QWidget

from usta.ui.platform.macos.overlay import MacOSOverlayRules


def wait_for_events(milliseconds=30):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


@unittest.skipUnless(os.environ.get('USTA_NATIVE_TESTS') == '1' and sys.platform == 'darwin', 'Requires macOS Cocoa')
class MacOSOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import AppKit
        import objc
        cls.cocoa = AppKit
        cls.objc = objc
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.widget = QWidget()
        self.widget.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.widget.setAttribute(Qt.WA_ShowWithoutActivating)
        self.widget.resize(120, 40)
        self.widget.move(150, 150)
        self.widget.show()
        self.rules = MacOSOverlayRules(self.widget)
        self.rules.start()
        wait_for_events()

    def tearDown(self):
        self.rules.stop()
        self.widget.close()
        self.widget.deleteLater()
        wait_for_events()

    def native_window(self):
        return self.objc.objc_object(c_void_p=int(self.widget.winId())).window()

    def assert_rules(self):
        window = self.native_window()
        behavior = int(window.collectionBehavior())
        self.assertEqual(window.level(), 25)
        self.assertEqual(behavior & 273, 273)
        if hasattr(self.cocoa, 'NSWindowCollectionBehaviorCanJoinAllApplications'):
            self.assertTrue(behavior & 262144)
            self.assertFalse(behavior & (65536 | 131072))
        self.assertFalse(window.hidesOnDeactivate())
        self.assertTrue(int(window.styleMask()) & 128)

    def reset_rules(self):
        window = self.native_window()
        window.setStyleMask_(window.styleMask() & ~128)
        window.setCollectionBehavior_(0)
        window.setLevel_(0)
        window.setHidesOnDeactivate_(True)

    def test_sets_fullscreen_and_all_applications_rules(self):
        self.assert_rules()

    def test_overlay_remains_on_screen_during_another_apps_native_fullscreen(self):
        import Quartz
        from usta.ui.overlay_window import TransparentOverlay

        self.rules.stop()
        self.widget.close()
        self.widget.deleteLater()
        # Exercise the real translation update path without global keyboard hooks.
        with mock.patch('usta.ui.overlay_window.GlobalHotkey', autospec=True):
            self.widget = TransparentOverlay()
        self.widget.move(150, 150)
        self.widget.show()
        self.rules = self.widget._macos_rules
        wait_for_events()

        helper = Path(__file__).parents[1] / 'helpers' / 'macos_fullscreen_host.py'
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / 'state.json'
            exit_file = Path(directory) / 'exit'
            process = subprocess.Popen([sys.executable, str(helper), str(state_file), str(exit_file)])
            try:
                def wait_for_fullscreen(expected):
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        wait_for_events(50)
                        if state_file.exists():
                            try:
                                state = json.loads(state_file.read_text())
                            except json.JSONDecodeError:
                                continue
                            if state['fullscreen'] == expected:
                                self.assertTrue(state['active'], 'Fullscreen host must be focused')
                                return
                        self.assertIsNone(process.poll(), 'Fullscreen host exited unexpectedly')
                    self.fail('Native fullscreen transition did not complete')

                wait_for_fullscreen(True)
                wait_for_events(500)
                native = self.native_window()
                self.assertTrue(native.isOnActiveSpace(), 'Overlay stayed on the desktop Space')
                windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, 0)
                self.assertIn(native.windowNumber(), [w['kCGWindowNumber'] for w in windows])
                frontmost = self.cocoa.NSWorkspace.sharedWorkspace().frontmostApplication()
                self.assertEqual(frontmost.processIdentifier(), process.pid)
                self.assert_rules()
                for text in ('First translation', 'Second translation', 'Third translation'):
                    self.widget.update_text(text)
                    wait_for_events(150)
                    frontmost = self.cocoa.NSWorkspace.sharedWorkspace().frontmostApplication()
                    self.assertEqual(frontmost.processIdentifier(), process.pid,
                                     'Translation update stole fullscreen focus')
                    self.assertEqual(self.widget.label.text(), text)
                    self.assertTrue(self.widget.hide_timer.isActive())
                    self.assertTrue(native.isOnActiveSpace())
                exit_file.touch()
                wait_for_fullscreen(False)
                wait_for_events(500)
                self.assertTrue(native.isOnActiveSpace())
                self.assert_rules()
            finally:
                process.terminate()
                process.wait(timeout=5)

    def test_older_cocoa_keeps_existing_fullscreen_rules(self):
        cocoa = self.cocoa

        class OlderCocoa:
            def __getattr__(self, name):
                if name == 'NSWindowCollectionBehaviorCanJoinAllApplications':
                    raise AttributeError(name)
                return getattr(cocoa, name)

        # PyObjC lazily reloads deleted constants, so simulate the older module.
        with mock.patch.dict(sys.modules, {'AppKit': OlderCocoa()}):
            self.reset_rules()
            self.app.sendEvent(self.widget, QEvent(QEvent.WindowStateChange))
            wait_for_events()
            self.assertEqual(int(self.native_window().collectionBehavior()), 273)
            self.assertEqual(self.native_window().level(), 25)

    def test_space_transition_restores_rules_after_late_native_reset(self):
        center = self.cocoa.NSWorkspace.sharedWorkspace().notificationCenter()
        center.postNotificationName_object_(self.cocoa.NSWorkspaceActiveSpaceDidChangeNotification, None)
        wait_for_events()
        self.reset_rules()
        wait_for_events(450)
        self.assert_rules()

    def test_window_state_change_restores_rules(self):
        self.reset_rules()
        self.app.sendEvent(self.widget, QEvent(QEvent.WindowStateChange))
        wait_for_events()
        self.assert_rules()

    def test_fullscreen_notifications_restore_rules(self):
        center = self.cocoa.NSNotificationCenter.defaultCenter()
        for name in (self.cocoa.NSWindowDidEnterFullScreenNotification,
                     self.cocoa.NSWindowDidExitFullScreenNotification):
            with self.subTest(notification=name):
                self.reset_rules()
                center.postNotificationName_object_(name, self.native_window())
                wait_for_events()
                self.assert_rules()

    def test_stop_cancels_pending_restore_and_restart_works(self):
        center = self.cocoa.NSWorkspace.sharedWorkspace().notificationCenter()
        name = self.cocoa.NSWorkspaceActiveSpaceDidChangeNotification
        center.postNotificationName_object_(name, None)
        self.rules.stop()
        self.reset_rules()
        center.postNotificationName_object_(name, None)
        wait_for_events(450)
        self.assertEqual(self.native_window().level(), 0)
        self.rules.start()
        wait_for_events()
        self.assert_rules()
